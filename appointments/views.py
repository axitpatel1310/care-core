from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AppointmentForm
from .models import Appointment

@login_required
@permission_required(
    "appointments.view_appointment",
    raise_exception=True,
)
def appointment_list(request):

    appointments = (
        Appointment.objects
        .select_related(
            "resident",
            "assigned_staff",
            "assigned_staff__user",
        )
        .order_by(
            "appointment_date",
            "start_time",
        )
    )

    query = request.GET.get("q", "").strip()

    if query:

        appointments = appointments.filter(
            Q(title__icontains=query)
            |
            Q(provider__icontains=query)
            |
            Q(location__icontains=query)
            |
            Q(
                resident__first_name__icontains=query
            )
            |
            Q(
                resident__last_name__icontains=query
            )
        )

    status = request.GET.get("status")

    if status:
        appointments = appointments.filter(
            status=status
        )

    appointment_type = request.GET.get(
        "appointment_type"
    )

    if appointment_type:
        appointments = appointments.filter(
            appointment_type=appointment_type
        )

    return render(
        request,
        "appointments/appointment_list.html",
        {
            "appointments": appointments,
            "query": query,
            "status": status,
            "appointment_type": appointment_type,
            "status_choices": Appointment.STATUS_CHOICES,
            "type_choices": Appointment.TYPE_CHOICES,
        },
    )
    
@login_required
@permission_required(
    "appointments.add_appointment",
    raise_exception=True,
)
def appointment_create(request):

    resident_id = request.GET.get("resident")

    initial = {}

    if resident_id:
        initial["resident"] = resident_id

    if request.method == "POST":

        form = AppointmentForm(request.POST)

        if form.is_valid():

            appointment = form.save()

            messages.success(
                request,
                "Appointment created successfully.",
            )

            return redirect(
                "appointment_detail",
                pk=appointment.pk,
            )

    else:

        form = AppointmentForm(
            initial=initial
        )

    return render(
        request,
        "appointments/appointment_form.html",
        {
            "form": form,
            "title": "Create Appointment",
            "button_text": "Create Appointment",
        },
    )
    
@login_required
@permission_required(
    "appointments.view_appointment",
    raise_exception=True,
)
def appointment_detail(request, pk):

    appointment = get_object_or_404(
        Appointment.objects.select_related(
            "resident",
            "assigned_staff",
            "assigned_staff__user",
        ),
        pk=pk,
    )

    return render(
        request,
        "appointments/appointment_detail.html",
        {
            "appointment": appointment,
        },
    )
    
@login_required
@permission_required(
    "appointments.change_appointment",
    raise_exception=True,
)
def appointment_edit(request, pk):

    appointment = get_object_or_404(
        Appointment,
        pk=pk,
    )

    if request.method == "POST":

        form = AppointmentForm(
            request.POST,
            instance=appointment,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Appointment updated successfully.",
            )

            return redirect(
                "appointment_detail",
                pk=appointment.pk,
            )

    else:

        form = AppointmentForm(
            instance=appointment,
        )

    return render(
        request,
        "appointments/appointment_form.html",
        {
            "form": form,
            "appointment": appointment,
            "title": "Edit Appointment",
            "button_text": "Save Changes",
        },
    )
    
@login_required
@permission_required(
    "appointments.delete_appointment",
    raise_exception=True,
)
def appointment_delete(request, pk):

    appointment = get_object_or_404(
        Appointment,
        pk=pk,
    )

    if request.method == "POST":

        appointment.delete()

        messages.success(
            request,
            "Appointment deleted.",
        )

        return redirect(
            "appointment_list"
        )

    return render(
        request,
        "appointments/appointment_delete.html",
        {
            "appointment": appointment,
        },
    )