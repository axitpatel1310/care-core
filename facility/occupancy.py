"""
Derived occupancy.

Room.occupied, Facility.occupancy and Facility.number_of_rooms are kept as
stored columns (so lists stay cheap to render) but are never edited by
hand: they are recalculated from residents and rooms whenever those change.
"""

from django.db.models import Count, Q

from .models import Facility, Room


# A resident on hospital stay or leave keeps their bed.
OCCUPYING_STATUSES = ("active", "hospital", "leave")


def occupants(room, exclude=None):

    residents = room.residents.filter(status__in=OCCUPYING_STATUSES)

    if exclude is not None and exclude.pk:
        residents = residents.exclude(pk=exclude.pk)

    return residents


def refresh_room(room_id):

    if room_id is None:
        return

    room = Room.objects.filter(pk=room_id).select_related("ward").first()

    if room is None:
        return

    Room.objects.filter(pk=room.pk).update(occupied=occupants(room).count())

    refresh_facility(room.ward.facility_id)


def refresh_facility(facility_id):

    if facility_id is None:
        return

    totals = Room.objects.filter(ward__facility_id=facility_id).aggregate(
        rooms=Count("id", distinct=True),
        residents=Count(
            "residents",
            filter=Q(residents__status__in=OCCUPYING_STATUSES),
        ),
    )

    Facility.objects.filter(pk=facility_id).update(
        number_of_rooms=totals["rooms"],
        occupancy=totals["residents"],
    )


def refresh_all():

    for room_id in Room.objects.values_list("pk", flat=True):
        refresh_room(room_id)

    for facility_id in Facility.objects.values_list("pk", flat=True):
        refresh_facility(facility_id)
