from django.contrib import admin

from .models import Facility, Room, Ward


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("name", "manager", "number_of_rooms", "occupancy", "status")
    readonly_fields = ("number_of_rooms", "occupancy")


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ("name", "facility")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_number", "ward", "capacity", "occupied")
    readonly_fields = ("occupied",)
