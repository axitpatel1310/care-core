from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("title", "resident", "appointment_type", "appointment_date", "start_time", "status")
    list_filter = ("status", "appointment_type")
