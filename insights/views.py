import csv
from datetime import timedelta
from functools import wraps

from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.audit import create_audit_log
from accounts.scoping import scope_for_model
from appointments.models import Appointment
from care.models import CareTask
from facility.models import Ward
from incidents.models import Incident
from medications.models import MedicationAdministration
from observations.models import Observation
from residents.models import Resident

from . import analytics
from .alerts import CRITICAL, INFO, SEVERITY_LABELS, WARNING, alerts_for
from .context_processors import alert_cache_key
from .risk import assess_residents


ANALYTICS_ROLES = ("admin", "manager", "rn")

PERIOD_CHOICES = [
    (30, "Last 30 days"),
    (90, "Last 90 days"),
    (180, "Last 6 months"),
    (365, "Last 12 months"),
]


def analytics_access_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not (request.user.is_superuser or request.user.role in ANALYTICS_ROLES):
            raise PermissionDenied

        return view_func(request, *args, **kwargs)

    return login_required(wrapper)


def user_scope(user):
    """A function limiting querysets to the facilities `user` may see."""

    def scope(queryset):
        return scope_for_model(queryset, user)

    return scope


def selected_period(request, default=90):

    try:
        days = int(request.GET.get("days", default))
    except ValueError:
        days = default

    if days not in dict(PERIOD_CHOICES):
        days = default

    return days


@login_required
def alert_centre(request):

    all_alerts = alerts_for(request.user)

    severity = request.GET.get("severity", "")

    alerts = [
        alert for alert in all_alerts
        if not severity or alert.severity == severity
    ]

    # Opening the alert centre refreshes the cached bell count.
    cache.delete(alert_cache_key(request.user))

    grouped = {}

    for alert in alerts:
        grouped.setdefault(alert.category, []).append(alert)

    return render(
        request,
        "insights/alerts.html",
        {
            "alerts": alerts,
            "grouped": grouped,
            "severity": severity,
            "severity_choices": [
                (CRITICAL, SEVERITY_LABELS[CRITICAL]),
                (WARNING, SEVERITY_LABELS[WARNING]),
                (INFO, SEVERITY_LABELS[INFO]),
            ],
            "counts": {
                level: sum(1 for alert in all_alerts if alert.severity == level)
                for level in (CRITICAL, WARNING, INFO)
            },
        },
    )


@login_required
@permission_required(
    "residents.view_resident",
    raise_exception=True,
)
def risk_register(request):

    residents = scope_for_model(Resident.objects.all(), request.user).filter(
        status="active",
    ).select_related("room")

    ward = request.GET.get("ward", "")

    if ward:
        residents = residents.filter(room__ward_id=ward)

    assessments = assess_residents(residents)

    band = request.GET.get("band", "")

    if band:
        assessments = [item for item in assessments if item.band == band]

    return render(
        request,
        "insights/risk_register.html",
        {
            "assessments": assessments,
            "band": band,
            "ward": ward,
            "wards": scope_for_model(Ward.objects.select_related("facility"), request.user),
        },
    )


@analytics_access_required
def analytics_dashboard(request):

    days = selected_period(request)
    start, end = analytics.period_bounds(days)
    scope = user_scope(request.user)

    chart_data = {
        "incidents_by_month": analytics.incidents_by_month(start, end, scope),
        "incidents_by_category": analytics.incidents_by_category(start, end, scope),
        "adherence": analytics.medication_adherence_by_week(start, end, scope),
        "news2": analytics.latest_news2_distribution(scope),
        "care_levels": analytics.residents_by_care_level(scope),
    }

    return render(
        request,
        "insights/analytics.html",
        {
            "days": days,
            "period_choices": PERIOD_CHOICES,
            "kpis": analytics.kpis(start, end, scope),
            "chart_data": chart_data,
            "start": start,
            "end": end,
        },
    )


def _export_incidents(start, end, scope):

    yield [
        "ID", "Date", "Resident", "Category", "Severity", "Status",
        "Reported by", "Description", "Immediate action", "Resolved at",
    ]

    for incident in (
        scope(Incident.objects.all())
        .filter(incident_date__range=(start, end))
        .select_related("resident", "reported_by__user")
        .order_by("incident_date")
    ):
        yield [
            incident.pk,
            timezone.localtime(incident.incident_date).strftime("%Y-%m-%d %H:%M"),
            incident.resident or "",
            incident.get_category_display(),
            incident.get_severity_display(),
            incident.get_status_display(),
            incident.reported_by or "",
            incident.description,
            incident.immediate_action,
            timezone.localtime(incident.resolved_at).strftime("%Y-%m-%d %H:%M") if incident.resolved_at else "",
        ]


def _export_medications(start, end, scope):

    yield ["Date", "Resident", "Medication", "Dose", "Route", "Status", "Staff", "Notes"]

    for administration in (
        scope(MedicationAdministration.objects.all())
        .filter(administered_at__range=(start, end))
        .select_related("medication__resident", "administered_by__user")
        .order_by("administered_at")
    ):
        medication = administration.medication
        yield [
            timezone.localtime(administration.administered_at).strftime("%Y-%m-%d %H:%M"),
            medication.resident,
            medication.name,
            medication.dose,
            medication.route,
            administration.get_status_display(),
            administration.administered_by or "",
            administration.notes,
        ]


def _export_observations(start, end, scope):

    yield [
        "Recorded", "Resident", "NEWS2", "Risk", "Resp. rate", "SpO2", "SpO2 scale",
        "On O2", "Systolic", "Diastolic", "Pulse", "ACVPU", "Temp", "Staff",
    ]

    for obs in (
        scope(Observation.objects.all())
        .filter(recorded_at__range=(start, end))
        .select_related("resident", "recorded_by__user")
        .order_by("recorded_at")
    ):
        yield [
            timezone.localtime(obs.recorded_at).strftime("%Y-%m-%d %H:%M"),
            obs.resident,
            obs.news2_score,
            obs.get_risk_level_display(),
            obs.respiratory_rate,
            obs.spo2,
            obs.spo2_scale,
            "Yes" if obs.on_oxygen else "No",
            obs.systolic_bp,
            obs.diastolic_bp or "",
            obs.pulse,
            obs.consciousness,
            obs.temperature,
            obs.recorded_by or "",
        ]


def _export_tasks(start, end, scope):

    yield ["Due date", "Due time", "Resident", "Task", "Type", "Priority", "Status", "Assigned to", "Completed at"]

    for task in (
        scope(CareTask.objects.all())
        .filter(due_date__range=(timezone.localdate(start), timezone.localdate(end)))
        .select_related("resident", "assigned_to__user")
        .order_by("due_date", "due_time")
    ):
        yield [
            task.due_date.isoformat(),
            task.due_time.strftime("%H:%M") if task.due_time else "",
            task.resident,
            task.title,
            task.get_task_type_display(),
            task.get_priority_display(),
            task.get_status_display(),
            task.assigned_to or "",
            timezone.localtime(task.completed_at).strftime("%Y-%m-%d %H:%M") if task.completed_at else "",
        ]


EXPORTS = {
    "incidents": ("incidents.view_incident", _export_incidents),
    "medication-administrations": ("medications.view_medicationadministration", _export_medications),
    "observations": ("observations.view_observation", _export_observations),
    "care-tasks": ("care.view_caretask", _export_tasks),
}


@analytics_access_required
def export_csv(request, dataset):

    if dataset not in EXPORTS:
        raise Http404

    permission, rows = EXPORTS[dataset]

    if not request.user.has_perm(permission):
        raise PermissionDenied

    days = selected_period(request)
    start, end = analytics.period_bounds(days)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="carecore-{dataset}-{timezone.localdate():%Y%m%d}.csv"'
    )

    writer = csv.writer(response)

    for row in rows(start, end, user_scope(request.user)):
        writer.writerow([_safe_cell(value) for value in row])

    create_audit_log(
        user=request.user,
        action="other",
        module="insights",
        description=f"Exported {dataset} CSV for the last {days} days.",
    )

    return response


def _safe_cell(value):
    """Neutralise spreadsheet formula injection in exported free text."""

    value = "" if value is None else str(value)

    if value[:1] in ("=", "+", "-", "@") and not value.lstrip("-").replace(".", "", 1).isdigit():
        return "'" + value

    return value


@login_required
@permission_required(
    "residents.view_resident",
    raise_exception=True,
)
def shift_handover(request):

    try:
        hours = int(request.GET.get("hours", 12))
    except ValueError:
        hours = 12

    hours = min(max(hours, 1), 72)

    now = timezone.now()
    since = now - timedelta(hours=hours)
    today = timezone.localdate(now)

    residents = (
        scope_for_model(Resident.objects.all(), request.user)
        .filter(status="active")
        .select_related("room__ward")
        .order_by("room__ward__name", "room__room_number", "last_name")
    )

    ward = request.GET.get("ward", "")

    if ward:
        residents = residents.filter(room__ward_id=ward)

    risks = {
        risk.resident.pk: risk
        for risk in assess_residents(residents, now=now)
    }

    entries = []

    for resident in residents:

        risk = risks[resident.pk]

        entries.append({
            "resident": resident,
            "risk": risk,
            "latest_obs": resident.observations.order_by("-recorded_at").first(),
            "obs_count": resident.observations.filter(recorded_at__gte=since).count(),
            "doses_not_given": (
                MedicationAdministration.objects
                .filter(
                    medication__resident=resident,
                    administered_at__gte=since,
                )
                .exclude(status="administered")
                .select_related("medication")
            ),
            "incidents": resident.incidents.filter(incident_date__gte=since),
            "outstanding_tasks": resident.care_tasks.filter(
                status__in=["pending", "in_progress"],
                due_date__lte=today,
            ),
            "appointments": Appointment.objects.filter(
                resident=resident,
                appointment_date__range=(today, today + timedelta(days=1)),
            ).exclude(status__in=["cancelled", "completed"]),
        })

    return render(
        request,
        "insights/handover.html",
        {
            "entries": entries,
            "hours": hours,
            "since": since,
            "generated_at": now,
            "ward": ward,
            "wards": scope_for_model(Ward.objects.select_related("facility"), request.user),
        },
    )
