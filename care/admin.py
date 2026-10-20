from django.contrib import admin

from .models import Assessment, CarePlan, CareTask, CognitiveBehaviouralSupport


@admin.register(CarePlan)
class CarePlanAdmin(admin.ModelAdmin):
    list_display = ("resident", "status", "next_review", "responsible_staff")
    list_filter = ("status",)


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("resident", "assessment_type", "assessment_date", "next_review")
    list_filter = ("assessment_type",)


@admin.register(CareTask)
class CareTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "resident", "priority", "status", "due_date", "assigned_to")
    list_filter = ("status", "priority", "task_type")


admin.site.register(CognitiveBehaviouralSupport)
