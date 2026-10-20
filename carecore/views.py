from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from residents.models import Resident
from staff.models import StaffMember
from appointments.models import Appointment
from incidents.models import Incident
from care.models import CareTask
from insights.alerts import CRITICAL, WARNING, alerts_for
from insights.risk import BAND_HIGH, assess_residents

@login_required
def dashboard(request):

    today = timezone.localdate()

    residents_count = Resident.objects.filter(
        status="active"
    ).count()

    staff_count = StaffMember.objects.count()

    appointments_today = Appointment.objects.filter(
        appointment_date=today
    ).select_related(
        "resident",
        "assigned_staff",
    )

    open_incidents = Incident.objects.filter(
        status__in=[
            "open",
            "investigating",
        ]
    ).select_related(
        "resident",
    )

    critical_incidents = Incident.objects.filter(
        severity="critical",
    ).exclude(
        status="resolved"
    ).select_related(
        "resident",
    )

    alerts = alerts_for(request.user)

    risk_assessments = []

    if request.user.has_perm("residents.view_resident"):
        risk_assessments = assess_residents(
            Resident.objects.filter(status="active").select_related("room")
        )

    context = {
        "today": today,

        "priority_alerts": [
            alert for alert in alerts
            if alert.severity in (CRITICAL, WARNING)
        ][:6],

        "alerts_count": len(alerts),

        "residents_at_risk": risk_assessments[:5],

        "high_risk_count": sum(
            1 for item in risk_assessments if item.band == BAND_HIGH
        ),

        "overdue_tasks_count": CareTask.objects.filter(
            status__in=["pending", "in_progress"],
            due_date__lt=today,
        ).count(),

        "residents_count": residents_count,

        "staff_count": staff_count,

        "appointments_today": appointments_today,

        "appointments_today_count": appointments_today.count(),

        "open_incidents": open_incidents,

        "open_incidents_count": open_incidents.count(),

        "critical_incidents": critical_incidents,

        "critical_incidents_count": critical_incidents.count(),
    }

    return render(
        request,
        "dashboard.html",
        context,
    )