from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from residents.models import Resident

from .models import Room
from .occupancy import refresh_facility, refresh_room


@receiver(pre_save, sender=Resident)
def remember_previous_room(sender, instance, raw=False, **kwargs):

    instance._previous_room_id = None

    if instance.pk and not raw:
        instance._previous_room_id = (
            Resident.objects.filter(pk=instance.pk)
            .values_list("room_id", flat=True)
            .first()
        )


@receiver(post_save, sender=Resident)
def update_occupancy_on_resident_save(sender, instance, raw=False, **kwargs):

    if raw:
        return

    refresh_room(instance.room_id)

    previous = getattr(instance, "_previous_room_id", None)

    if previous and previous != instance.room_id:
        refresh_room(previous)


@receiver(post_delete, sender=Resident)
def update_occupancy_on_resident_delete(sender, instance, **kwargs):
    refresh_room(instance.room_id)


@receiver(post_save, sender=Room)
def update_facility_on_room_save(sender, instance, created, raw=False, **kwargs):

    if raw:
        return

    if created:
        refresh_facility(instance.ward.facility_id)


@receiver(post_delete, sender=Room)
def update_facility_on_room_delete(sender, instance, **kwargs):
    refresh_facility(instance.ward.facility_id)
