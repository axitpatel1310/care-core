from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from residents.models import Resident
from .forms import MedicationForm
from .models import Medication
from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from staff.models import StaffMember
from .forms import (
    MedicationAdministrationForm,
    MedicationForm,
)
from .models import (
    Medication,
    MedicationAdministration,
)

@login_required
@permission_required(
    "medications.view_medication",
    raise_exception=True,
)
def medication_list(request):

    medications = (
        Medication.objects
        .select_related("resident")
        .order_by(
            "resident__last_name",
            "name",
        )
    )

    status = request.GET.get("status")

    if status:
        medications = medications.filter(
            status=status
        )

    query = request.GET.get("q", "").strip()

    if query:
        medications = medications.filter(
            name__icontains=query
        )

    return render(
        request,
        "medications/medication_list.html",
        {
            "medications": medications,
            "status": status,
            "query": query,
            "status_choices": (
                Medication.STATUS_CHOICES
            ),
        },
    )

@login_required
@permission_required(
    "medications.add_medication",
    raise_exception=True,
)
def medication_create(request):

    resident_id = request.GET.get(
        "resident"
    )

    initial = {}

    if resident_id:
        initial["resident"] = resident_id

    if request.method == "POST":

        form = MedicationForm(
            request.POST
        )

        if form.is_valid():

            medication = form.save()

            messages.success(
                request,
                "Medication added successfully.",
            )

            return redirect(
                "medication_detail",
                pk=medication.pk,
            )

    else:

        form = MedicationForm(
            initial=initial
        )

    return render(
        request,
        "medications/medication_form.html",
        {
            "form": form,
            "title": "Add Medication",
            "button_text": "Add Medication",
        },
    )

@login_required
@permission_required(
    "medications.view_medication",
    raise_exception=True,
)
def medication_detail(request, pk):

    medication = get_object_or_404(
        Medication.objects.select_related("resident"),
        pk=pk,
    )

    administrations = (
        medication.administrations
        .select_related("administered_by")
        .order_by("-administered_at")
    )

    return render(
        request,
        "medications/medication_detail.html",
        {
            "medication": medication,
            "administrations": administrations,
        },
    )
    
@login_required
@permission_required(
    "medications.change_medication",
    raise_exception=True,
)
def medication_edit(request, pk):

    medication = get_object_or_404(
        Medication,
        pk=pk,
    )

    if request.method == "POST":

        form = MedicationForm(
            request.POST,
            instance=medication,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Medication updated successfully.",
            )

            return redirect(
                "medication_detail",
                pk=medication.pk,
            )

    else:

        form = MedicationForm(
            instance=medication
        )

    return render(
        request,
        "medications/medication_form.html",
        {
            "form": form,
            "medication": medication,
            "title": "Edit Medication",
            "button_text": "Save Changes",
        },
    )
@login_required
@permission_required(
    "medications.delete_medication",
    raise_exception=True,
)
def medication_delete(request, pk):

    medication = get_object_or_404(
        Medication,
        pk=pk,
    )

    if request.method == "POST":

        medication.delete()

        messages.success(
            request,
            "Medication deleted.",
        )

        return redirect(
            "medication_list"
        )

    return render(
        request,
        "medications/medication_delete.html",
        {
            "medication": medication,
        },
    )
from django.utils import timezone

from .models import Medication, MedicationAdministration
from .forms import MedicationForm, MedicationAdministrationForm

@login_required
@permission_required(
    "medications.view_medicationadministration",
    raise_exception=True,
)
def administration_list(request):

    administrations = (
        MedicationAdministration.objects
        .select_related(
            "medication",
            "medication__resident",
            "administered_by",
        )
        .order_by("-administered_at")
    )

    query = request.GET.get("q", "").strip()

    if query:

        administrations = administrations.filter(
            Q(
                medication__name__icontains=query
            )
            |
            Q(
                medication__resident__first_name__icontains=query
            )
            |
            Q(
                medication__resident__last_name__icontains=query
            )
        )

    return render(
        request,
        "medications/administration_list.html",
        {
            "administrations": administrations,
            "query": query,
        },
    )


@login_required
@permission_required(
    "medications.add_medicationadministration",
    raise_exception=True,
)

@login_required
@permission_required(
    "medications.add_medicationadministration",
    raise_exception=True,
)
def administration_create(request, medication_id):

    medication = get_object_or_404(
        Medication,
        pk=medication_id,
    )

    if request.method == "POST":

        form = MedicationAdministrationForm(
            request.POST
        )

        if form.is_valid():

            administration = form.save(
                commit=False
            )

            administration.medication = medication

            staff_member = getattr(
                request.user,
                "staff_member",
                None,
            )

            if staff_member:
                administration.administered_by = staff_member

            administration.save()

            messages.success(
                request,
                "Medication administration recorded successfully.",
            )

            return redirect(
                "medication_detail",
                pk=medication.pk,
            )

    else:

        form = MedicationAdministrationForm()

    return render(
        request,
        "medications/administration_form.html",
        {
            "form": form,
            "medication": medication,
        },
    )

@login_required
@permission_required(
    "medications.view_medicationadministration",
    raise_exception=True,
)
def medication_administration_history(
    request,
    medication_id,
):
    medication = get_object_or_404(
        Medication,
        pk=medication_id,
    )

    administrations = (
        medication.administrations
        .select_related(
            "administered_by",
            "administered_by__user",
        )
        .order_by("-administered_at")
    )

    return render(
        request,
        "medications/administration_history.html",
        {
            "medication": medication,
            "administrations": administrations,
        },
    )

@login_required
@permission_required(
    "medications.view_medicationadministration",
    raise_exception=True,
)
def administration_detail(request, pk):

    administration = get_object_or_404(
        MedicationAdministration.objects.select_related(
            "medication",
            "medication__resident",
            "administered_by",
        ),
        pk=pk,
    )

    return render(
        request,
        "medications/administration_detail.html",
        {
            "administration": administration,
        },
    )


@login_required
@permission_required(
    "medications.change_medicationadministration",
    raise_exception=True,
)
def administration_edit(request, pk):

    administration = get_object_or_404(
        MedicationAdministration,
        pk=pk,
    )

    if request.method == "POST":

        form = MedicationAdministrationForm(
            request.POST,
            instance=administration,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Administration record updated.",
            )

            return redirect(
                "administration_detail",
                pk=administration.pk,
            )

    else:

        form = MedicationAdministrationForm(
            instance=administration
        )

    return render(
        request,
        "medications/administration_form.html",
        {
            "form": form,
            "administration": administration,
            "title": "Edit Administration Record",
            "button_text": "Save Changes",
        },
    )


@login_required
@permission_required(
    "medications.delete_medicationadministration",
    raise_exception=True,
)
def administration_delete(request, pk):

    administration = get_object_or_404(
        MedicationAdministration,
        pk=pk,
    )

    if request.method == "POST":

        administration.delete()

        messages.success(
            request,
            "Administration record deleted.",
        )

        return redirect(
            "administration_list"
        )

    return render(
        request,
        "medications/administration_delete.html",
        {
            "administration": administration,
        },
    )

@login_required
@permission_required(
    "medications.view_medicationadministration",
    raise_exception=True,
)
def administration_history(
    request,
    medication_pk,
):

    medication = get_object_or_404(
        Medication.objects.select_related(
            "resident"
        ),
        pk=medication_pk,
    )

    administrations = (
        medication.administrations
        .select_related(
            "administered_by",
            "administered_by__user",
        )
        .order_by(
            "-administered_at"
        )
    )

    return render(
        request,
        "medications/administration_history.html",
        {
            "medication": medication,
            "administrations": administrations,
        },
    )

from datetime import date

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from .models import Medication


@login_required
@permission_required(
    "medications.view_medication",
    raise_exception=True,
)
def medication_due_today(request):

    medications = (
        Medication.objects
        .filter(
            status="active",
            start_date__lte=date.today(),
        )
        .filter(
            end_date__isnull=True
        )
        .select_related("resident")
        .order_by(
            "resident__last_name",
            "name",
        )
    )

    return render(
        request,
        "medications/due_today.html",
        {
            "medications": medications,
            "today": date.today(),
        },
    )