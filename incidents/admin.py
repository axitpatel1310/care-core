from django.contrib import admin

from .models import Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("id", "resident", "category", "severity", "status", "incident_date")
    list_filter = ("status", "severity", "category")
