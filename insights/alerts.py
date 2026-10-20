"""
Rule-based clinical and governance alert engine.

Each rule inspects live data and yields Alert objects. Rules declare the
permission needed to see them, so staff only receive alerts for records
they are allowed to view.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from appointments.models import Appointment
from care.models import Assessment, CarePlan, CareTask
from compliance.models import ComplianceDocument, CorrectiveAction, Risk
from incidents.models import Incident
from medications.models import Medication, MedicationAdministration
from observations.models import Observation
from observations.news2 import CLINICAL_RESPONSE, RISK_HIGH, RISK_LOW, RISK_MEDIUM


CRITICAL = "critical"
WARNING = "warning"
INFO = "info"

SEVERITY_ORDER = {
    CRITICAL: 0,
    WARNING: 1,
    INFO: 2,
}

SEVERITY_LABELS = {
    CRITICAL: "Critical",
    WARNING: "Warning",
    INFO: "Information",
}


@dataclass
class Alert:
    severity: str
    category: str
    title: str
    message: str
    url: str = ""
    resident: object = None

    @property
    def severity_label(self):
        return SEVERITY_LABELS[self.severity]


RULES = []


def rule(permission):
    """Register an alert rule that is only evaluated for users holding `permission`."""

    def decorator(func):
        RULES.append((permission, func))
        return func

    return decorator


def latest_observations():
    """The most recent observation for every resident who has one."""

    latest = {}

    for observation in (
        Observation.objects
        .filter(resident__status="active")
        .select_related("resident")
        .order_by("resident_id", "-recorded_at")
    ):
        latest.setdefault(observation.resident_id, observation)

    return latest.values()


@rule("observations.view_observation")
def deteriorating_residents(now):

    for observation in latest_observations():

        if observation.recorded_at < now - timedelta(hours=24):
            continue

        if observation.risk_level not in (RISK_MEDIUM, RISK_HIGH) and not observation.has_red_score:
            continue

        severity = CRITICAL if observation.risk_level == RISK_HIGH else WARNING

        yield Alert(
            severity=severity,
            category="Deterioration",
            title=f"{observation.resident}: NEWS2 {observation.news2_score}",
            message=(
                f"{observation.get_risk_level_display()} clinical risk recorded "
                f"{timezone.localtime(observation.recorded_at):%d %b %H:%M}."
            ),
            url=reverse("observation_detail", args=[observation.pk]),
            resident=observation.resident,
        )


@rule("observations.view_observation")
def observations_overdue(now):
    """Repeat observations not taken within the NEWS2 monitoring interval."""

    for observation in latest_observations():

        if observation.risk_level == RISK_LOW:
            continue

        hours = CLINICAL_RESPONSE[observation.risk_level]["monitoring_hours"] or 1
        due = observation.recorded_at + timedelta(hours=hours)

        if due >= now:
            continue

        yield Alert(
            severity=WARNING,
            category="Observations",
            title=f"{observation.resident}: repeat observations overdue",
            message=(
                f"NEWS2 {observation.news2_score} requires observations at least every "
                f"{hours} hour{'s' if hours != 1 else ''}; last set "
                f"{timezone.localtime(observation.recorded_at):%d %b %H:%M}."
            ),
            url=reverse("resident_observations", args=[observation.resident_id]),
            resident=observation.resident,
        )


@rule("incidents.view_incident")
def serious_open_incidents(now):

    incidents = (
        Incident.objects
        .filter(severity__in=["high", "critical"])
        .exclude(status="resolved")
        .select_related("resident")
    )

    for incident in incidents:
        yield Alert(
            severity=CRITICAL if incident.severity == "critical" else WARNING,
            category="Incidents",
            title=f"{incident.get_severity_display()} incident #{incident.pk} unresolved",
            message=(
                f"{incident.get_category_display()}"
                f"{' – ' + str(incident.resident) if incident.resident else ''} "
                f"({incident.get_status_display().lower()})."
            ),
            url=reverse("incident_detail", args=[incident.pk]),
            resident=incident.resident,
        )


@rule("care.view_caretask")
def overdue_care_tasks(now):

    today = timezone.localdate(now)

    tasks = (
        CareTask.objects
        .filter(status__in=["pending", "in_progress"])
        .filter(due_date__lte=today)
        .select_related("resident")
    )

    for task in tasks:

        overdue = task.due_date < today or (
            task.due_time is not None
            and task.due_time < timezone.localtime(now).time()
        )

        if not overdue and task.priority != "urgent":
            continue

        yield Alert(
            severity=WARNING if overdue or task.priority == "urgent" else INFO,
            category="Care tasks",
            title=f"{'Overdue' if overdue else 'Urgent'} task: {task.title}",
            message=(
                f"{task.resident} – due {task.due_date:%d %b}"
                f"{' ' + task.due_time.strftime('%H:%M') if task.due_time else ''}."
            ),
            url=reverse("task_detail", args=[task.pk]),
            resident=task.resident,
        )


@rule("medications.view_medicationadministration")
def doses_not_given(now):

    administrations = (
        MedicationAdministration.objects
        .filter(
            status__in=["missed", "refused", "withheld"],
            administered_at__gte=now - timedelta(hours=24),
        )
        .select_related("medication", "medication__resident")
    )

    for administration in administrations:
        yield Alert(
            severity=WARNING,
            category="Medication",
            title=(
                f"{administration.medication.name} "
                f"{administration.get_status_display().lower()}"
            ),
            message=(
                f"{administration.medication.resident} – "
                f"{timezone.localtime(administration.administered_at):%d %b %H:%M}."
            ),
            url=reverse("administration_detail", args=[administration.pk]),
            resident=administration.medication.resident,
        )


@rule("medications.view_medication")
def medications_ending_soon(now):

    today = timezone.localdate(now)

    medications = (
        Medication.objects
        .filter(
            status="active",
            end_date__gte=today,
            end_date__lte=today + timedelta(days=3),
        )
        .select_related("resident")
    )

    for medication in medications:
        yield Alert(
            severity=INFO,
            category="Medication",
            title=f"{medication.name} course ends {medication.end_date:%d %b}",
            message=f"{medication.resident} – review whether a new prescription is required.",
            url=reverse("medication_detail", args=[medication.pk]),
            resident=medication.resident,
        )


@rule("care.view_careplan")
def care_plan_reviews_due(now):

    today = timezone.localdate(now)

    plans = (
        CarePlan.objects
        .filter(status="active", next_review__lt=today)
        .select_related("resident")
    )

    for plan in plans:
        yield Alert(
            severity=INFO,
            category="Reviews",
            title=f"Care plan review overdue: {plan.resident}",
            message=f"Review was due {plan.next_review:%d %b %Y}.",
            url=reverse("care_plan_detail", args=[plan.pk]),
            resident=plan.resident,
        )


@rule("care.view_assessment")
def assessment_reviews_due(now):

    today = timezone.localdate(now)

    assessments = (
        Assessment.objects
        .filter(next_review__lt=today)
        .select_related("resident")
    )

    for assessment in assessments:
        yield Alert(
            severity=INFO,
            category="Reviews",
            title=f"{assessment.get_assessment_type_display()} reassessment overdue",
            message=f"{assessment.resident} – due {assessment.next_review:%d %b %Y}.",
            url=reverse("assessment_detail", args=[assessment.pk]),
            resident=assessment.resident,
        )


@rule("appointments.view_appointment")
def unconfirmed_appointments(now):

    today = timezone.localdate(now)

    appointments = (
        Appointment.objects
        .filter(
            appointment_date__gte=today,
            appointment_date__lte=today + timedelta(days=1),
            status="scheduled",
        )
        .select_related("resident")
    )

    for appointment in appointments:
        yield Alert(
            severity=INFO,
            category="Appointments",
            title=f"Unconfirmed appointment: {appointment.title}",
            message=(
                f"{appointment.resident} – {appointment.appointment_date:%d %b} "
                f"at {appointment.start_time:%H:%M}."
            ),
            url=reverse("appointment_detail", args=[appointment.pk]),
            resident=appointment.resident,
        )


@rule("compliance.view_correctiveaction")
def overdue_corrective_actions(now):

    actions = CorrectiveAction.objects.filter(
        status__in=["open", "in_progress"],
        due_date__lt=timezone.localdate(now),
    )

    for action in actions:
        yield Alert(
            severity=WARNING if action.priority in ("high", "critical") else INFO,
            category="Compliance",
            title=f"Corrective action overdue: {action.title}",
            message=f"Due {action.due_date:%d %b %Y} ({action.get_priority_display()} priority).",
            url=reverse("corrective_action_detail", args=[action.pk]),
        )


@rule("compliance.view_compliancedocument")
def documents_due_review(now):

    documents = ComplianceDocument.objects.filter(
        status="active",
        next_review__lt=timezone.localdate(now),
    )

    for document in documents:
        yield Alert(
            severity=INFO,
            category="Compliance",
            title=f"Policy review overdue: {document.title}",
            message=f"Version {document.version} was due for review {document.next_review:%d %b %Y}.",
            url=reverse("document_detail", args=[document.pk]),
        )


@rule("compliance.view_risk")
def risk_reviews_due(now):

    risks = Risk.objects.exclude(status="resolved").filter(
        review_date__lt=timezone.localdate(now),
    )

    for risk in risks:
        yield Alert(
            severity=WARNING if risk.severity in ("high", "extreme") else INFO,
            category="Compliance",
            title=f"Risk review overdue: {risk.description}",
            message=f"Rated {risk.get_severity_display()}; review was due {risk.review_date:%d %b %Y}.",
            url=reverse("risk_detail", args=[risk.pk]),
        )


def alerts_for(user, now=None):

    now = now or timezone.now()

    alerts = []

    for permission, evaluate in RULES:
        if user.has_perm(permission):
            alerts.extend(evaluate(now))

    alerts.sort(key=lambda alert: SEVERITY_ORDER[alert.severity])

    return alerts
