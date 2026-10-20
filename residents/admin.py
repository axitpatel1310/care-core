from django.contrib import admin

from .models import Resident, ResidentContact


class ResidentContactInline(admin.TabularInline):
    model = ResidentContact
    extra = 0


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "room", "status", "care_level", "admission_date")
    list_filter = ("status", "care_level")
    search_fields = ("first_name", "last_name")
    inlines = [ResidentContactInline]
