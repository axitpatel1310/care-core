from django.contrib import admin

from .models import Observation


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ("resident", "recorded_at", "news2_score", "risk_level", "recorded_by")
    list_filter = ("risk_level", "has_red_score")
    search_fields = ("resident__first_name", "resident__last_name")
    readonly_fields = ("news2_score", "risk_level", "has_red_score", "escalation_task")
