from django.contrib import admin

from .models import Medication, MedicationAdministration, MedicationDoseTime


class MedicationDoseTimeInline(admin.TabularInline):
    model = MedicationDoseTime
    extra = 0


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("name", "resident", "dose", "route", "as_required", "status")
    list_filter = ("status", "as_required")
    inlines = [MedicationDoseTimeInline]


@admin.register(MedicationAdministration)
class MedicationAdministrationAdmin(admin.ModelAdmin):
    list_display = ("medication", "scheduled_for", "administered_at", "status", "administered_by")
    list_filter = ("status",)
