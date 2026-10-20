from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuditLog, User


@admin.register(User)
class CareCoreUserAdmin(UserAdmin):
    list_display = ("email", "first_name", "last_name", "role", "is_active", "last_login")
    list_filter = ("role", "is_active")
    fieldsets = UserAdmin.fieldsets + (("CareCore", {"fields": ("role",)}),)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "module", "description")
    list_filter = ("action", "module")
    search_fields = ("description", "user__email")

    # The audit trail is append-only, including for administrators.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
