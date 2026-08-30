from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .models import Resident, ResidentContact
from care.models import CarePlan
from .forms import ResidentForm
from .models import Resident
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from care.models import CarePlan, Assessment, CognitiveBehaviouralSupport
from medications.models import Medication, MedicationAdministration

from .forms import ResidentForm, ResidentContactForm
from .models import Resident, ResidentContact

@login_required
@permission_required(
    "residents.view_resident",
    raise_exception=True,
)
def resident_list(request):

    residents = Resident.objects.select_related(
        "room",
        "room__ward",
    ).all()

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    care_level = request.GET.get("care_level", "").strip()

    if query:
        residents = residents.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )

    if status:
        residents = residents.filter(
            status=status
        )

    if care_level:
        residents = residents.filter(
            care_level=care_level
        )

    residents = residents.order_by(
        "last_name",
        "first_name",
    )

    return render(
        request,
        "residents/list.html",
        {
            "residents": residents,
            "query": query,
            "status": status,
            "care_level": care_level,
        },
    )


@login_required
@permission_required(
    "residents.add_resident",
    raise_exception=True,
)
def resident_create(request):

    if request.method == "POST":

        form = ResidentForm(request.POST)

        if form.is_valid():

            resident = form.save()

            messages.success(
                request,
                "Resident created successfully.",
            )

            return redirect(
                "resident_detail",
                pk=resident.pk,
            )

    else:

        form = ResidentForm()

    return render(
        request,
        "residents/form.html",
        {
            "form": form,
            "title": "Add Resident",
            "button_text": "Create Resident",
        },
    )


from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render

from .models import Resident

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Resident


@login_required
def resident_detail(request, pk):

    resident = get_object_or_404(
        Resident.objects.prefetch_related(
            "contacts",
            "care_plans",
            "assessments",
            "care_tasks",
            "medications",
            "incidents",
            "appointments",
        ),
        pk=pk,
    )

    return render(
        request,
        "residents/detail.html",
        {
            "resident": resident,
            "care_tasks": resident.care_tasks.all(),
            "care_plans": resident.care_plans.all(),
            "assessments": resident.assessments.all(),
            "medications": resident.medications.all(),
            "incidents": resident.incidents.all(),
            "appointments": resident.appointments.all(),
        },
    )
    
@login_required
@permission_required(
    "residents.change_resident",
    raise_exception=True,
)
def resident_edit(request, pk):

    resident = get_object_or_404(
        Resident,
        pk=pk,
    )

    if request.method == "POST":

        form = ResidentForm(
            request.POST,
            instance=resident,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Resident updated successfully.",
            )

            return redirect(
                "resident_detail",
                pk=resident.pk,
            )

    else:

        form = ResidentForm(
            instance=resident,
        )

    return render(
        request,
        "residents/form.html",
        {
            "form": form,
            "resident": resident,
            "title": "Edit Resident",
            "button_text": "Save Changes",
        },
    )


@login_required
@permission_required(
    "residents.delete_resident",
    raise_exception=True,
)
def resident_delete(request, pk):

    resident = get_object_or_404(
        Resident,
        pk=pk,
    )

    if request.method == "POST":

        resident.delete()

        messages.success(
            request,
            "Resident deleted successfully.",
        )

        return redirect("resident_list")

    return render(
        request,
        "residents/delete.html",
        {
            "resident": resident,
        },
    )
    
@login_required
@permission_required(
    "residents.view_residentcontact",
    raise_exception=True,
)
def contact_detail(request, pk):

    contact = get_object_or_404(
        ResidentContact.objects.select_related(
            "resident",
        ),
        pk=pk,
    )

    return render(
        request,
        "residents/contacts/detail.html",
        {
            "contact": contact,
        },
    )


@login_required
@permission_required(
    "residents.add_residentcontact",
    raise_exception=True,
)
def contact_create(request, resident_pk):

    resident = get_object_or_404(
        Resident,
        pk=resident_pk,
    )

    if request.method == "POST":

        form = ResidentContactForm(
            request.POST
        )

        if form.is_valid():

            contact = form.save(
                commit=False
            )

            contact.resident = resident

            contact.save()

            messages.success(
                request,
                "Contact added successfully.",
            )

            return redirect(
                "resident_detail",
                pk=resident.pk,
            )

    else:

        form = ResidentContactForm()

    return render(
        request,
        "residents/contacts/form.html",
        {
            "form": form,
            "resident": resident,
            "title": "Add Contact",
            "button_text": "Add Contact",
        },
    )


@login_required
@permission_required(
    "residents.change_residentcontact",
    raise_exception=True,
)
def contact_edit(request, pk):

    contact = get_object_or_404(
        ResidentContact.objects.select_related(
            "resident",
        ),
        pk=pk,
    )

    if request.method == "POST":

        form = ResidentContactForm(
            request.POST,
            instance=contact,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Contact updated successfully.",
            )

            return redirect(
                "resident_detail",
                pk=contact.resident.pk,
            )

    else:

        form = ResidentContactForm(
            instance=contact,
        )

    return render(
        request,
        "residents/contacts/form.html",
        {
            "form": form,
            "resident": contact.resident,
            "contact": contact,
            "title": "Edit Contact",
            "button_text": "Save Changes",
        },
    )

from .models import Resident, ResidentContact

@login_required
@permission_required(
    "residents.delete_residentcontact",
    raise_exception=True,
)
def contact_delete(request, pk):

    contact = get_object_or_404(
        ResidentContact.objects.select_related(
            "resident",
        ),
        pk=pk,
    )

    resident = contact.resident

    if request.method == "POST":

        contact.delete()

        messages.success(
            request,
            "Contact deleted successfully.",
        )

        return redirect(
            "resident_detail",
            pk=resident.pk,
        )

    return render(
        request,
        "residents/contacts/delete.html",
        {
            "contact": contact,
            "resident": resident,
        },
    )