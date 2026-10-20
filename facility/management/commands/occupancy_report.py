from django.core.management.base import BaseCommand
from django.db.models import F

from facility.models import Room
from facility.occupancy import occupants, refresh_all
from residents.models import Resident


class Command(BaseCommand):

    help = (
        "Recalculate room and facility occupancy, then list rooms over capacity "
        "and residents with no facility, which need a person to resolve."
    )

    def handle(self, *args, **options):

        refresh_all()

        over = Room.objects.filter(occupied__gt=F("capacity")).select_related("ward__facility")

        for room in over:
            names = ", ".join(str(resident) for resident in occupants(room))
            self.stdout.write(self.style.WARNING(
                f"{room.ward} / room {room}: {room.occupied} of {room.capacity} beds – {names}"
            ))

        unassigned = Resident.objects.filter(facility__isnull=True)

        for resident in unassigned:
            self.stdout.write(self.style.WARNING(
                f"{resident} has no facility (visible to administrators only)"
            ))

        if not over and not unassigned:
            self.stdout.write(self.style.SUCCESS("All rooms are within capacity and every resident has a facility."))
