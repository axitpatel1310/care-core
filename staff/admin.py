from django.contrib import admin

from .models import ResidentStaffAssignment, StaffMember


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "employee_id", "facility", "ward", "employment_status")
    list_filter = ("facility", "employment_status")


@admin.register(ResidentStaffAssignment)
class ResidentStaffAssignmentAdmin(admin.ModelAdmin):
    list_display = ("staff", "resident", "role", "is_active", "start_date")
