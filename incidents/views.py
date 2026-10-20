from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import IncidentForm
from .models import Incident
from .models import Incident

@login_required
@permission_required(
    "incidents.view_incident",
    raise_exception=True,
)
def incident_list(request):

    incidents = (
        Incident.objects
        .select_related(
            "resident",
            "reported_by",
            "reported_by__user",
        )
        .order_by("-incident_date")
    )

    query = request.GET.get("q", "").strip()

    if query:

        incidents = incidents.filter(
            Q(
                description__icontains=query
            )
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
        incidents = incidents.filter(
            status=status
        )

    severity = request.GET.get("severity")

    if severity:
        incidents = incidents.filter(
            severity=severity
        )

    category = request.GET.get("category")

    if category:
        incidents = incidents.filter(
            category=category
        )

    return render(
        request,
        "incident/incident_list.html",
        {
            "incidents": incidents,
            "query": query,
            "status": status,
            "severity": severity,
            "category": category,
            "status_choices": Incident.STATUS_CHOICES,
            "severity_choices": Incident.SEVERITY_CHOICES,
            "category_choices": Incident.CATEGORY_CHOICES,
        },
    )

@login_required
@permission_required(
    "incidents.add_incident",
    raise_exception=True,
)
def incident_create(request):

    resident_id = request.GET.get("resident")

    initial = {}

    if resident_id:
        initial["resident"] = resident_id

    if request.method == "POST":

        form = IncidentForm(request.POST)

        if form.is_valid():

            incident = form.save(commit=False)

            staff_member = getattr(
                request.user,
                "staff_profile",
                None,
            )

            if staff_member:
                incident.reported_by = staff_member

            incident.save()
            messages.success(
                request,
                "Incident reported successfully.",
            )

            return redirect(
                "incident_detail",
                pk=incident.pk,
            )

    else:

        form = IncidentForm(
            initial=initial
        )

    return render(
        request,
        "incident/incident_form.html",
        {
            "form": form,
            "title": "Report Incident",
            "button_text": "Report Incident",
        },
    )

@login_required
@permission_required(
    "incidents.view_incident",
    raise_exception=True,
)
def incident_detail(request, pk):

    incident = get_object_or_404(
        Incident.objects.select_related(
            "resident",
            "reported_by",
            "reported_by__user",
        ),
        pk=pk,
    )

    return render(
        request,
        "incident/incident_detail.html",
        {
            "incident": incident,
        },
    )

from .forms import IncidentForm, IncidentInvestigationForm
@login_required
@permission_required(
    "incidents.change_incident",
    raise_exception=True,
)
def incident_investigate(request, pk):

    incident = get_object_or_404(
        Incident,
        pk=pk,
    )

    if request.method == "POST":

        form = IncidentInvestigationForm(
            request.POST,
            instance=incident,
        )

        if form.is_valid():

            incident = form.save(commit=False)

            if incident.status == "resolved":

                incident.resolved_at = timezone.now()

            else:

                incident.resolved_at = None

            incident.save()

            messages.success(
                request,
                "Incident investigation updated successfully.",
            )

            return redirect(
                "incident_detail",
                pk=incident.pk,
            )

    else:

        form = IncidentInvestigationForm(
            instance=incident,
        )

    return render(
        request,
        "incident/incident_investigate.html",
        {
            "form": form,
            "incident": incident,
        },
    )    

@login_required
@permission_required(
    "incidents.change_incident",
    raise_exception=True,
)
def incident_edit(request, pk):

    incident = get_object_or_404(
        Incident,
        pk=pk,
    )

    if request.method == "POST":

        form = IncidentForm(
            request.POST,
            instance=incident,
        )

        if form.is_valid():

            incident = form.save(commit=False)

            if incident.status == "resolved":

                if not incident.resolved_at:
                    incident.resolved_at = timezone.now()

            else:

                incident.resolved_at = None

            incident.save()

            messages.success(
                request,
                "Incident updated successfully.",
            )

            return redirect(
                "incident_detail",
                pk=incident.pk,
            )

    else:

        form = IncidentForm(
            instance=incident,
        )

    return render(
        request,
        "incident/incident_form.html",
        {
            "form": form,
            "incident": incident,
            "title": "Edit Incident",
            "button_text": "Save Changes",
        },
    )
    
@login_required
@permission_required(
    "incidents.change_incident",
    raise_exception=True,
)
def incident_resolve(request, pk):

    incident = get_object_or_404(
        Incident,
        pk=pk,
    )

    if request.method == "POST":

        incident.status = "resolved"
        incident.resolved_at = timezone.now()

        incident.save(
            update_fields=[
                "status",
                "resolved_at",
            ]
        )

        messages.success(
            request,
            "Incident marked as resolved.",
        )

    return redirect(
        "incident_detail",
        pk=incident.pk,
    )
    
@login_required
@permission_required(
    "incidents.delete_incident",
    raise_exception=True,
)
def incident_delete(request, pk):

    incident = get_object_or_404(
        Incident,
        pk=pk,
    )

    if request.method == "POST":
        incident.delete()

        messages.success(
            request,
            "Incident deleted.",
        )

        return redirect(
            "incident_list"
        )

    return render(
        request,
        "incident/incident_delete.html",
        {
            "incident": incident,
        },
    )
    