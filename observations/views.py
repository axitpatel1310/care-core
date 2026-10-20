from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from residents.models import Resident

from .forms import ObservationForm
from .models import Observation
from .news2 import CLINICAL_RESPONSE, RISK_CHOICES
from .services import escalate_if_required


BREAKDOWN_LABELS = {
    "respiratory_rate": "Respiration rate",
    "spo2": "SpO₂",
    "air_or_oxygen": "Air or oxygen",
    "systolic_bp": "Systolic blood pressure",
    "pulse": "Pulse",
    "consciousness": "Consciousness",
    "temperature": "Temperature",
}


@login_required
@permission_required(
    "observations.view_observation",
    raise_exception=True,
)
def observation_list(request):

    observations = Observation.objects.select_related(
        "resident",
        "recorded_by",
        "recorded_by__user",
    )

    risk = request.GET.get("risk", "")
    query = request.GET.get("q", "").strip()

    if risk:
        observations = observations.filter(risk_level=risk)

    if query:
        observations = observations.filter(
            Q(resident__first_name__icontains=query)
            | Q(resident__last_name__icontains=query)
        )

    return render(
        request,
        "observations/observation_list.html",
        {
            "observations": observations[:200],
            "risk": risk,
            "query": query,
            "risk_choices": RISK_CHOICES,
        },
    )


@login_required
@permission_required(
    "observations.add_observation",
    raise_exception=True,
)
def observation_create(request):

    initial = {}

    resident_id = request.GET.get("resident")

    if resident_id:
        initial["resident"] = resident_id

    if request.method == "POST":

        form = ObservationForm(request.POST)

        if form.is_valid():

            observation = form.save(commit=False)

            observation.recorded_by = getattr(
                request.user,
                "staff_profile",
                None,
            )

            observation.save()

            task = escalate_if_required(observation)

            if task:
                messages.warning(
                    request,
                    f"NEWS2 score {observation.news2_score}: "
                    f"{observation.result.response} "
                    "An urgent care task has been created.",
                )
            else:
                messages.success(
                    request,
                    f"Observations recorded. NEWS2 score {observation.news2_score}.",
                )

            return redirect(
                "observation_detail",
                pk=observation.pk,
            )

    else:

        form = ObservationForm(initial=initial)

    return render(
        request,
        "observations/observation_form.html",
        {
            "form": form,
            "title": "Record Observations",
            "button_text": "Save & Calculate NEWS2",
        },
    )


@login_required
@permission_required(
    "observations.view_observation",
    raise_exception=True,
)
def observation_detail(request, pk):

    observation = get_object_or_404(
        Observation.objects.select_related(
            "resident",
            "recorded_by__user",
            "escalation_task",
        ),
        pk=pk,
    )

    result = observation.result

    breakdown = [
        (BREAKDOWN_LABELS[key], score)
        for key, score in result.breakdown.items()
    ]

    return render(
        request,
        "observations/observation_detail.html",
        {
            "observation": observation,
            "result": result,
            "breakdown": breakdown,
        },
    )


@login_required
@permission_required(
    "observations.delete_observation",
    raise_exception=True,
)
def observation_delete(request, pk):

    observation = get_object_or_404(
        Observation,
        pk=pk,
    )

    if request.method == "POST":

        resident_pk = observation.resident_id

        observation.delete()

        messages.success(
            request,
            "Observation record deleted.",
        )

        return redirect(
            "resident_observations",
            resident_pk=resident_pk,
        )

    return render(
        request,
        "observations/observation_delete.html",
        {
            "observation": observation,
        },
    )


@login_required
@permission_required(
    "observations.view_observation",
    raise_exception=True,
)
def resident_observations(request, resident_pk):

    resident = get_object_or_404(
        Resident,
        pk=resident_pk,
    )

    observations = resident.observations.select_related(
        "recorded_by__user",
    )

    # Oldest first for the trend chart, limited to the most recent 30 readings.
    chart_points = list(observations[:30])[::-1]

    chart_data = {
        "labels": [
            obs.recorded_at.strftime("%d %b %H:%M")
            for obs in chart_points
        ],
        "news2": [obs.news2_score for obs in chart_points],
        "pulse": [obs.pulse for obs in chart_points],
        "systolic": [obs.systolic_bp for obs in chart_points],
        "respiratory": [obs.respiratory_rate for obs in chart_points],
        "spo2": [obs.spo2 for obs in chart_points],
        "temperature": [float(obs.temperature) for obs in chart_points],
    }

    latest = observations.first()

    return render(
        request,
        "observations/resident_observations.html",
        {
            "resident": resident,
            "observations": observations,
            "latest": latest,
            "chart_data": chart_data,
            "clinical_response": CLINICAL_RESPONSE,
        },
    )
