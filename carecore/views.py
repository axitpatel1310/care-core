from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from residents.models import Resident
from staff.models import StaffMember
from appointments.models import Appointment
from incidents.models import Incident

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

    context = {
        "today": today,

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