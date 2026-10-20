from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.shortcuts import redirect, render

from accounts.scoping import (
    get_visible_object_or_404,
    limit_resident_choices,
    scope_for_model,
)
from carecore.pagination import paginate

from .forms import (
    FacilityForm,
    RoomForm,
    WardForm,
)
from .models import (
    Facility,
    Room,
    Ward,
)


# =========================================================
# FACILITY
# =========================================================

@login_required
@permission_required(
    "facility.view_facility",
    raise_exception=True,
)
def facility_list(request):

    facilities = scope_for_model(
        Facility.objects.select_related(
            "manager"
        ).all(),
        request.user,
    )

    page, filter_query = paginate(request, facilities)

    return render(
        request,
        "facility/list.html",
        {
            "facilities": page,
            "page": page,
            "filter_query": filter_query,
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
        limit_resident_choices(form, request.user)

        if form.is_valid():

            form.save()

            return redirect("facility_list")

    else:

        form = FacilityForm()
        limit_resident_choices(form, request.user)

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

    facility = get_visible_object_or_404(
        request.user,
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

    facility = get_visible_object_or_404(
        request.user,
        Facility,
        pk=pk,
    )

    if request.method == "POST":

        form = FacilityForm(
            request.POST,
            instance=facility,
        )
        limit_resident_choices(form, request.user)

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
        limit_resident_choices(form, request.user)

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

    facility = get_visible_object_or_404(
        request.user,
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
            "object": facility,
            "object_type": "facility",
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
        limit_resident_choices(form, request.user)

        if form.is_valid():

            ward = form.save()

            return redirect(
                "facility_detail",
                pk=ward.facility.pk,
            )

    else:

        form = WardForm()
        limit_resident_choices(form, request.user)

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

    ward = get_visible_object_or_404(
        request.user,
        Ward,
        pk=pk,
    )

    if request.method == "POST":

        form = WardForm(
            request.POST,
            instance=ward,
        )
        limit_resident_choices(form, request.user)

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
        limit_resident_choices(form, request.user)

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

    ward = get_visible_object_or_404(
        request.user,
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
        limit_resident_choices(form, request.user)

        if form.is_valid():

            room = form.save()

            return redirect(
                "facility_detail",
                pk=room.ward.facility.pk,
            )

    else:

        form = RoomForm()
        limit_resident_choices(form, request.user)

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

    room = get_visible_object_or_404(
        request.user,
        Room,
        pk=pk,
    )

    if request.method == "POST":

        form = RoomForm(
            request.POST,
            instance=room,
        )
        limit_resident_choices(form, request.user)

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
        limit_resident_choices(form, request.user)

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

    room = get_visible_object_or_404(
        request.user,
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
