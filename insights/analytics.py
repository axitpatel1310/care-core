"""
Aggregate quality indicators for the analytics dashboard.

All functions take a start/end datetime window so the same calculations can
back both the on-screen charts and exported reports.
"""

from collections import Counter, OrderedDict
from datetime import timedelta

from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone

from care.models import CareTask
from incidents.models import Incident
from medications.models import MedicationAdministration
from observations.models import Observation
from observations.news2 import RISK_CHOICES
from residents.models import Resident


def unscoped(queryset):
    return queryset


def period_bounds(days):
    end = timezone.now()
    return end - timedelta(days=days), end


def occupied_bed_days(start, end, scope=None):
    """
    Approximate occupied bed days in the window: each currently active
    resident contributes the days between max(admission, start) and end.
    """

    scope = scope or unscoped

    total = 0

    for admission_date in scope(Resident.objects.all()).filter(status="active").values_list(
        "admission_date", flat=True
    ):
        first_day = max(admission_date, timezone.localdate(start))
        total += max((timezone.localdate(end) - first_day).days, 0)

    return total


def kpis(start, end, scope=None):

    scope = scope or unscoped

    incidents = scope(Incident.objects.all()).filter(incident_date__range=(start, end))

    falls = incidents.filter(category="fall").count()
    bed_days = occupied_bed_days(start, end, scope)

    administrations = scope(MedicationAdministration.objects.all()).filter(
        administered_at__range=(start, end)
    )
    total_doses = administrations.count()
    given = administrations.filter(status="administered").count()

    due_tasks = scope(CareTask.objects.all()).filter(
        due_date__range=(timezone.localdate(start), timezone.localdate(end)),
    ).exclude(status="cancelled")
    completed = due_tasks.filter(status="completed", completed_at__isnull=False)
    on_time = sum(
        1 for task in completed.only("due_date", "completed_at")
        if timezone.localdate(task.completed_at) <= task.due_date
    )

    resolution = incidents.filter(
        status="resolved",
        resolved_at__isnull=False,
    ).aggregate(
        average=Avg(
            ExpressionWrapper(
                F("resolved_at") - F("incident_date"),
                output_field=DurationField(),
            )
        )
    )["average"]

    observations = scope(Observation.objects.all()).filter(recorded_at__range=(start, end))

    return {
        "incident_count": incidents.count(),
        "falls": falls,
        "falls_rate": round(falls / bed_days * 1000, 2) if bed_days else None,
        "bed_days": bed_days,
        "medication_adherence": round(given / total_doses * 100, 1) if total_doses else None,
        "doses_recorded": total_doses,
        "task_on_time_rate": round(on_time / due_tasks.count() * 100, 1) if due_tasks.exists() else None,
        "tasks_due": due_tasks.count(),
        "mean_resolution_hours": (
            round(resolution.total_seconds() / 3600, 1) if resolution is not None else None
        ),
        "observation_count": observations.count(),
        "escalations": observations.exclude(risk_level="low").count(),
    }


def incidents_by_month(start, end, scope=None):

    scope = scope or unscoped

    rows = (
        scope(Incident.objects.all())
        .filter(incident_date__range=(start, end))
        .annotate(month=TruncMonth("incident_date"))
        .values("month", "severity")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    months = OrderedDict()
    cursor = timezone.localdate(start).replace(day=1)
    last = timezone.localdate(end).replace(day=1)

    while cursor <= last:
        months[cursor] = Counter()
        cursor = (cursor + timedelta(days=32)).replace(day=1)

    for row in rows:
        month = timezone.localdate(row["month"]).replace(day=1)
        months.setdefault(month, Counter())[row["severity"]] += row["total"]

    return {
        "labels": [month.strftime("%b %Y") for month in months],
        "series": {
            label: [months[month][value] for month in months]
            for value, label in Incident.SEVERITY_CHOICES
        },
    }


def incidents_by_category(start, end, scope=None):

    scope = scope or unscoped

    labels = dict(Incident.CATEGORY_CHOICES)

    rows = (
        scope(Incident.objects.all())
        .filter(incident_date__range=(start, end))
        .values("category")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    return {
        "labels": [labels.get(row["category"], row["category"]) for row in rows],
        "values": [row["total"] for row in rows],
    }


def medication_adherence_by_week(start, end, scope=None):

    scope = scope or unscoped

    rows = (
        scope(MedicationAdministration.objects.all())
        .filter(administered_at__range=(start, end))
        .annotate(week=TruncWeek("administered_at"))
        .values("week", "status")
        .annotate(total=Count("id"))
        .order_by("week")
    )

    weeks = OrderedDict()

    for row in rows:
        weeks.setdefault(row["week"], Counter())[row["status"]] += row["total"]

    return {
        "labels": [week.strftime("%d %b") for week in weeks],
        "values": [
            round(counts["administered"] / sum(counts.values()) * 100, 1)
            for counts in weeks.values()
        ],
    }


def latest_news2_distribution(scope=None):

    scope = scope or unscoped

    latest = {}

    for resident_id, risk_level in (
        scope(Observation.objects.all())
        .filter(resident__status="active")
        .order_by("resident_id", "-recorded_at")
        .values_list("resident_id", "risk_level")
    ):
        latest.setdefault(resident_id, risk_level)

    counts = Counter(latest.values())

    return {
        "labels": [label for _, label in RISK_CHOICES],
        "values": [counts.get(value, 0) for value, _ in RISK_CHOICES],
    }


def residents_by_care_level(scope=None):

    scope = scope or unscoped

    labels = dict(Resident.CARE_LEVEL_CHOICES)

    rows = (
        scope(Resident.objects.all())
        .filter(status="active")
        .values("care_level")
        .annotate(total=Count("id"))
        .order_by("care_level")
    )

    return {
        "labels": [labels.get(row["care_level"], row["care_level"]) for row in rows],
        "values": [row["total"] for row in rows],
    }
