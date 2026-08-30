from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import FacilityForm, WardForm, RoomForm
from .models import Facility, Ward, Room


# =========================================================
# FACILITY
# =========================================================

@login_required
@permission_required(
    "facility.view_facility",
    raise_exception=True,
)
def facility_list(request):

    facilities = Facility.objects.select_related(
        "manager"
    ).all()

    return render(
        request,
        "facility/list.html",
        {
            "facilities": facilities,
        },
    )


@login_required
@permission_required(
    "facility.add_facility",
    raise_exception=True,
)
def facility_create(request):

    if request.method == "POST":

        form = FacilityForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect("facility_list")

    else:

        form = FacilityForm()

    return render(
        request,
        "facility/form.html",
        {
            "form": form,
            "title": "Add Facility",
            "button_text": "Create Facility",
        },
    )


@login_required
@permission_required(
    "facility.view_facility",
    raise_exception=True,
)
def facility_detail(request, pk):

    facility = get_object_or_404(
        Facility,
        pk=pk,
    )

    wards = facility.wards.prefetch_related(
        "rooms"
    ).all()

    return render(
        request,
        "facility/detail.html",
        {
            "facility": facility,
            "wards": wards,
        },
    )


@login_required
@permission_required(
    "facility.change_facility",
    raise_exception=True,
)
def facility_edit(request, pk):

    facility = get_object_or_404(
        Facility,
        pk=pk,
    )

    if request.method == "POST":

        form = FacilityForm(
            request.POST,
            instance=facility,
        )

        if form.is_valid():

            form.save()

            return redirect(
                "facility_detail",
                pk=facility.pk,
            )

    else:

        form = FacilityForm(
            instance=facility,
        )

    return render(
        request,
        "facility/form.html",
        {
            "form": form,
            "facility": facility,
            "title": "Edit Facility",
            "button_text": "Save Changes",
        },
    )


@login_required
@permission_required(
    "facility.delete_facility",
    raise_exception=True,
)
def facility_delete(request, pk):

    facility = get_object_or_404(
        Facility,
        pk=pk,
    )

    if request.method == "POST":

        facility.delete()

        return redirect("facility_list")

    return render(
        request,
        "facility/delete.html",
        {
            "facility": facility,
        },
    )


# =========================================================
# WARDS
# =========================================================

@login_required
@permission_required(
    "facility.add_ward",
    raise_exception=True,
)
def ward_create(request):

    if request.method == "POST":

        form = WardForm(request.POST)

        if form.is_valid():

            ward = form.save()

            return redirect(
                "facility_detail",
                pk=ward.facility.pk,
            )

    else:

        form = WardForm()

    return render(
        request,
        "facility/form.html",
        {
            "form": form,
            "title": "Add Ward",
            "button_text": "Create Ward",
        },
    )


@login_required
@permission_required(
    "facility.change_ward",
    raise_exception=True,
)
def ward_edit(request, pk):

    ward = get_object_or_404(
        Ward,
        pk=pk,
    )

    if request.method == "POST":

        form = WardForm(
            request.POST,
            instance=ward,
        )

        if form.is_valid():

            ward = form.save()

            return redirect(
                "facility_detail",
                pk=ward.facility.pk,
            )

    else:

        form = WardForm(
            instance=ward,
        )

    return render(
        request,
        "facility/form.html",
        {
            "form": form,
            "title": "Edit Ward",
            "button_text": "Save Changes",
        },
    )


@login_required
@permission_required(
    "facility.delete_ward",
    raise_exception=True,
)
def ward_delete(request, pk):

    ward = get_object_or_404(
        Ward,
        pk=pk,
    )

    facility_id = ward.facility.pk

    if request.method == "POST":

        ward.delete()

        return redirect(
            "facility_detail",
            pk=facility_id,
        )

    return render(
        request,
        "facility/delete.html",
        {
            "object": ward,
            "object_type": "ward",
        },
    )


# =========================================================
# ROOMS
# =========================================================

@login_required
@permission_required(
    "facility.add_room",
    raise_exception=True,
)
def room_create(request):

    if request.method == "POST":

        form = RoomForm(request.POST)

        if form.is_valid():

            room = form.save()

            return redirect(
                "facility_detail",
                pk=room.ward.facility.pk,
            )

    else:

        form = RoomForm()

    return render(
        request,
        "facility/form.html",
        {
            "form": form,
            "title": "Add Room",
            "button_text": "Create Room",
        },
    )


@login_required
@permission_required(
    "facility.change_room",
    raise_exception=True,
)
def room_edit(request, pk):

    room = get_object_or_404(
        Room,
        pk=pk,
    )

    if request.method == "POST":

        form = RoomForm(
            request.POST,
            instance=room,
        )

        if form.is_valid():

            room = form.save()

            return redirect(
                "facility_detail",
                pk=room.ward.facility.pk,
            )

    else:

        form = RoomForm(
            instance=room,
        )

    return render(
        request,
        "facility/form.html",
        {
            "form": form,
            "title": "Edit Room",
            "button_text": "Save Changes",
        },
    )


@login_required
@permission_required(
    "facility.delete_room",
    raise_exception=True,
)
def room_delete(request, pk):

    room = get_object_or_404(
        Room,
        pk=pk,
    )

    facility_id = room.ward.facility.pk

    if request.method == "POST":

        room.delete()

        return redirect(
            "facility_detail",
            pk=facility_id,
        )

    return render(
        request,
        "facility/delete.html",
        {
            "object": room,
            "object_type": "room",
        },
    )