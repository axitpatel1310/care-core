from django.contrib import admin

from .models import (
    Audit,
    AuditControl,
    ComplianceDocument,
    CorrectiveAction,
    Risk,
)


class AuditControlInline(admin.TabularInline):
    model = AuditControl
    extra = 0


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "start_date", "completion_date")
    inlines = [AuditControlInline]


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = ("description", "category", "likelihood", "impact", "severity", "status")
    list_filter = ("severity", "status", "category")


admin.site.register(ComplianceDocument)
admin.site.register(CorrectiveAction)
