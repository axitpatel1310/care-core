from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.db.models import Q
from django.http import Http404
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from accounts.scoping import scope, scope_residents
from carecore.pagination import paginate
from residents.models import Resident

from .forms import (
    MedicationAdministrationForm,
    MedicationForm,
)
from .models import (
    Medication,
    MedicationAdministration,
)
from .schedule import (
    active_medications,
    doses_for_day,
    scheduled_datetime,
    scheduled_doses,
)


def visible_medications(user):
    return scope(Medication.objects.all(), user)


def visible_administrations(user):
    return scope(MedicationAdministration.objects.all(), user, prefix="medication__resident__")


@login_required
@permission_required(
    "medications.view_medication",
    raise_exception=True,
)
def medication_list(request):

    medications = (
        visible_medications(request.user)
        .select_related("resident")
        .prefetch_related("dose_times")
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
            Q(name__icontains=query)
            | Q(resident__first_name__icontains=query)
            | Q(resident__last_name__icontains=query)
        )

    page, filter_query = paginate(request, medications)

    return render(
        request,
        "medications/medication_list.html",
        {
            "medications": page,
            "page": page,
            "filter_query": filter_query,
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

    initial = {}

    resident_id = request.GET.get("resident")

    if resident_id:
        initial["resident"] = resident_id

    if request.method == "POST":

        form = MedicationForm(request.POST)
        form.fields["resident"].queryset = scope_residents(Resident.objects.all(), request.user)

        if form.is_valid():

            medication = form.save()

            messages.success(
                request,
                f"Medication added. Schedule: {medication.schedule_display}.",
            )

            return redirect(
                "medication_detail",
                pk=medication.pk,
            )

    else:

        form = MedicationForm(initial=initial)
        form.fields["resident"].queryset = scope_residents(Resident.objects.all(), request.user)

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
        visible_medications(request.user)
        .select_related("resident")
        .prefetch_related("dose_times"),
        pk=pk,
    )

    administrations = (
        medication.administrations
        .select_related("administered_by__user")
        .order_by("-administered_at")[:10]
    )

    today = timezone.localdate()

    return render(
        request,
        "medications/medication_detail.html",
        {
            "medication": medication,
            "administrations": administrations,
            "todays_doses": scheduled_doses([medication], today, today),
        },
    )


@login_required
@permission_required(
    "medications.change_medication",
    raise_exception=True,
)
def medication_edit(request, pk):

    medication = get_object_or_404(
        visible_medications(request.user),
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

    form.fields["resident"].queryset = scope_residents(Resident.objects.all(), request.user)

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
        visible_medications(request.user),
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


@login_required
@permission_required(
    "medications.view_medicationadministration",
    raise_exception=True,
)
def administration_list(request):

    administrations = (
        visible_administrations(request.user)
        .select_related(
            "medication",
            "medication__resident",
            "administered_by__user",
        )
        .order_by("-administered_at")
    )

    query = request.GET.get("q", "").strip()

    if query:

        administrations = administrations.filter(
            Q(medication__name__icontains=query)
            | Q(medication__resident__first_name__icontains=query)
            | Q(medication__resident__last_name__icontains=query)
        )

    page, filter_query = paginate(request, administrations)

    return render(
        request,
        "medications/administration_list.html",
        {
            "administrations": page,
            "page": page,
            "filter_query": filter_query,
            "query": query,
        },
    )


def requested_dose(request, medication):
    """
    The scheduled dose a "Record" link points at (?scheduled_for=ISO datetime),
    validated against the medication's actual dose times.
    """

    value = request.POST.get("scheduled_for") or request.GET.get("scheduled_for")

    if not value:
        return None

    when = parse_datetime(value)

    if when is None:
        raise Http404("Invalid scheduled dose.")

    if timezone.is_naive(when):
        when = timezone.make_aware(when)

    local = timezone.localtime(when)

    valid_times = {dose.time for dose in medication.dose_times.all()}

    if local.time().replace(second=0, microsecond=0) not in valid_times or not medication.is_active_on(local.date()):
        raise Http404("That dose is not on this medication's schedule.")

    return scheduled_datetime(local.date(), local.time().replace(second=0, microsecond=0))


@login_required
@permission_required(
    "medications.add_medicationadministration",
    raise_exception=True,
)
def administration_create(request, medication_id):

    medication = get_object_or_404(
        visible_medications(request.user)
        .select_related("resident")
        .prefetch_related("dose_times"),
        pk=medication_id,
    )

    scheduled_for = requested_dose(request, medication)

    instance = MedicationAdministration(
        medication=medication,
        scheduled_for=scheduled_for,
    )

    if request.method == "POST":

        form = MedicationAdministrationForm(
            request.POST,
            instance=instance,
            scheduled_for=scheduled_for,
        )

        if form.is_valid():

            administration = form.save(
                commit=False
            )

            administration.administered_by = getattr(
                request.user,
                "staff_profile",
                None,
            )

            administration.save()

            messages.success(
                request,
                "Medication administration recorded successfully.",
            )

            if request.POST.get("return_to") == "round":
                return redirect("medication_due_today")

            return redirect(
                "medication_detail",
                pk=medication.pk,
            )

    else:

        form = MedicationAdministrationForm(
            instance=instance,
            scheduled_for=scheduled_for,
            initial={
                "administered_at": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
                "status": "administered",
            },
        )

    return render(
        request,
        "medications/administration_form.html",
        {
            "form": form,
            "medication": medication,
            "scheduled_for": scheduled_for,
            "return_to": request.GET.get("return_to", ""),
        },
    )


@login_required
@permission_required(
    "medications.view_medicationadministration",
    raise_exception=True,
)
def administration_history(
    request,
    medication_pk=None,
    medication_id=None,
):

    medication = get_object_or_404(
        visible_medications(request.user).select_related(
            "resident"
        ),
        pk=medication_pk or medication_id,
    )

    administrations = (
        medication.administrations
        .select_related(
            "administered_by__user",
        )
        .order_by(
            "-administered_at"
        )
    )

    page, filter_query = paginate(request, administrations)

    return render(
        request,
        "medications/administration_history.html",
        {
            "medication": medication,
            "administrations": page,
            "page": page,
            "filter_query": filter_query,
        },
    )


# Both history URLs render the same record.
medication_administration_history = administration_history


@login_required
@permission_required(
    "medications.view_medicationadministration",
    raise_exception=True,
)
def administration_detail(request, pk):

    administration = get_object_or_404(
        visible_administrations(request.user).select_related(
            "medication",
            "medication__resident",
            "administered_by__user",
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
        visible_administrations(request.user),
        pk=pk,
    )

    if request.method == "POST":

        form = MedicationAdministrationForm(
            request.POST,
            instance=administration,
            scheduled_for=administration.scheduled_for,
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
            instance=administration,
            scheduled_for=administration.scheduled_for,
        )

    return render(
        request,
        "medications/administration_form.html",
        {
            "form": form,
            "administration": administration,
            "medication": administration.medication,
            "scheduled_for": administration.scheduled_for,
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
        visible_administrations(request.user),
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
    "medications.view_medication",
    raise_exception=True,
)
def medication_due_today(request):
    """The medication round: every scheduled dose today, grouped by dose time."""

    now = timezone.now()
    day = parse_date(request.GET.get("date", "")) or timezone.localdate(now)

    doses = doses_for_day(day, visible_medications(request.user), now=now)

    state = request.GET.get("state", "")

    counts = {}

    for dose in doses:
        counts[dose.state] = counts.get(dose.state, 0) + 1

    counts["not_given"] = sum(
        counts.get(key, 0) for key in ("refused", "missed", "withheld")
    )

    if state == "outstanding":
        doses = [dose for dose in doses if dose.is_outstanding]

    rounds = {}

    for dose in doses:
        rounds.setdefault(timezone.localtime(dose.scheduled_for).strftime("%H:%M"), []).append(dose)

    prn = (
        visible_medications(request.user)
        .filter(status="active", as_required=True)
        .select_related("resident")
    )

    return render(
        request,
        "medications/due_today.html",
        {
            "day": day,
            "is_today": day == timezone.localdate(now),
            "previous_day": day - timedelta(days=1),
            "next_day": day + timedelta(days=1),
            "rounds": rounds,
            "counts": counts,
            "state": state,
            "prn_medications": prn,
        },
    )


@login_required
@permission_required(
    "medications.view_medicationadministration",
    raise_exception=True,
)
def resident_mar(request, resident_pk):
    """A 7-day Medication Administration Record grid for one resident."""

    resident = get_object_or_404(
        scope_residents(Resident.objects.all(), request.user),
        pk=resident_pk,
    )

    today = timezone.localdate()
    start = parse_date(request.GET.get("start", "")) or today - timedelta(days=6)
    days = [start + timedelta(days=offset) for offset in range(7)]

    medications = list(
        active_medications(resident.medications.all())
        .filter(start_date__lte=days[-1])
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=days[0]))
    )

    doses = scheduled_doses(medications, days[0], days[-1])

    by_slot = {}

    for dose in doses:
        local = timezone.localtime(dose.scheduled_for)
        by_slot[(dose.medication.pk, local.time(), local.date())] = dose

    rows = []

    for medication in medications:
        for dose_time in medication.dose_times.all():
            rows.append({
                "medication": medication,
                "time": dose_time.time,
                "cells": [by_slot.get((medication.pk, dose_time.time, day)) for day in days],
            })

    prn_given = (
        MedicationAdministration.objects
        .filter(
            medication__resident=resident,
            scheduled_for__isnull=True,
            administered_at__date__gte=days[0],
            administered_at__date__lte=days[-1],
        )
        .select_related("medication", "administered_by__user")
        .order_by("administered_at")
    )

    return render(
        request,
        "medications/mar.html",
        {
            "resident": resident,
            "days": days,
            "rows": rows,
            "today": today,
            "previous_start": days[0] - timedelta(days=7),
            "next_start": days[0] + timedelta(days=7),
            "prn_given": prn_given,
        },
    )
