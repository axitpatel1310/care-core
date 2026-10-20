from datetime import timedelta

from django.utils import timezone

from care.models import CareTask

from .news2 import RISK_HIGH, RISK_MEDIUM


def responsible_staff_for(resident):
    """Prefer the resident's assigned nurse, then their primary carer."""

    assignments = resident.staff_assignments.filter(
        is_active=True,
    ).select_related("staff")

    for role in ("nurse", "primary", "manager"):
        assignment = assignments.filter(role=role).first()

        if assignment:
            return assignment.staff

    return None


def escalate_if_required(observation):
    """
    Create an urgent follow-up care task when the NEWS2 result needs a
    clinical response. Returns the created task, or None.
    """

    result = observation.result

    if not result.requires_escalation or observation.escalation_task_id:
        return None

    due_at = timezone.localtime(observation.recorded_at) + timedelta(
        hours=max(result.monitoring_hours, 0)
    )

    priority = "urgent" if result.risk_level in (RISK_MEDIUM, RISK_HIGH) else "high"

    task = CareTask.objects.create(
        resident=observation.resident,
        assigned_to=responsible_staff_for(observation.resident),
        title=(
            f"NEWS2 {result.total} ({observation.get_risk_level_display()} risk) – "
            "clinical review and repeat observations"
        ),
        description=result.response,
        task_type="health_check",
        priority=priority,
        due_date=due_at.date(),
        due_time=due_at.time().replace(second=0, microsecond=0),
    )

    observation.escalation_task = task
    observation.save(update_fields=["escalation_task"])

    return task
