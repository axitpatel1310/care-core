from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import generic

from incidents.models import Incident

from .forms import (
    AuditControlForm,
    AuditForm,
    ComplianceDocumentForm,
    CorrectiveActionForm,
    RiskForm,
)
from .models import (
    Audit,
    AuditControl,
    ComplianceDocument,
    CorrectiveAction,
    Risk,
)


@login_required
def compliance_dashboard(request):

    today = timezone.localdate()

    open_risks = Risk.objects.exclude(status="resolved")

    # 5x5 heat map: matrix[impact][likelihood] = number of open risks.
    cells = {
        (row["likelihood"], row["impact"]): row["total"]
        for row in open_risks.values("likelihood", "impact").annotate(total=Count("id"))
    }

    matrix = [
        {
            "impact": impact,
            "cells": [
                {
                    "likelihood": likelihood,
                    "score": likelihood * impact,
                    "count": cells.get((likelihood, impact), 0),
                }
                for likelihood in range(1, 6)
            ],
        }
        for impact in range(5, 0, -1)
    ]

    audits = Audit.objects.prefetch_related("controls").order_by("-start_date")

    actions = CorrectiveAction.objects.select_related("owner__user")

    context = {
        "documents": ComplianceDocument.objects.order_by("next_review"),
        "documents_due": ComplianceDocument.objects.filter(
            status="active",
            next_review__lt=today,
        ).count(),
        "risks": open_risks,
        "high_risks": open_risks.filter(severity__in=["high", "extreme"]).count(),
        "risk_matrix": matrix,
        "audits": audits,
        "actions": actions.filter(status__in=["open", "in_progress"]),
        "overdue_actions": actions.filter(
            status__in=["open", "in_progress"],
            due_date__lt=today,
        ).count(),
        "action_status": dict(
            actions.values_list("status").annotate(total=Count("id"))
        ),
    }

    return render(
        request,
        "compliance/dashboard.html",
        context,
    )


class CompliancePermissionMixin(LoginRequiredMixin, PermissionRequiredMixin):
    action = "view"

    def handle_no_permission(self):
        # Anonymous users go to the login page; signed-in users without the permission get a 403.
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()

    def get_permission_required(self):
        return [f"compliance.{self.action}_{self.model._meta.model_name}"]


class ComplianceFormMixin:
    template_name = "compliance/form.html"
    success_message = "Saved successfully."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["verbose_name"] = self.model._meta.verbose_name.title()
        context["list_url"] = reverse(self.list_url_name)
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response


class ComplianceDeleteView(CompliancePermissionMixin, generic.DeleteView):
    action = "delete"
    template_name = "compliance/confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["verbose_name"] = self.model._meta.verbose_name
        return context

    def form_valid(self, form):
        messages.success(self.request, f"{self.model._meta.verbose_name.capitalize()} deleted.")
        return super().form_valid(form)


# --------------------------------------------------------------------------
# Risk register
# --------------------------------------------------------------------------

class RiskList(CompliancePermissionMixin, generic.ListView):
    model = Risk
    template_name = "compliance/risk_list.html"
    context_object_name = "risks"

    def get_queryset(self):
        risks = Risk.objects.select_related("owner__user")
        status = self.request.GET.get("status")
        severity = self.request.GET.get("severity")
        if status:
            risks = risks.filter(status=status)
        if severity:
            risks = risks.filter(severity=severity)
        return risks

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            status=self.request.GET.get("status", ""),
            severity=self.request.GET.get("severity", ""),
            status_choices=Risk.STATUS_CHOICES,
            severity_choices=Risk.SEVERITY_CHOICES,
        )
        return context


class RiskDetail(CompliancePermissionMixin, generic.DetailView):
    model = Risk
    template_name = "compliance/risk_detail.html"
    context_object_name = "risk"


class RiskCreate(CompliancePermissionMixin, ComplianceFormMixin, generic.CreateView):
    model = Risk
    form_class = RiskForm
    action = "add"
    list_url_name = "risk_list"
    success_message = "Risk added to the register."

    def get_success_url(self):
        return reverse("risk_detail", args=[self.object.pk])


class RiskUpdate(CompliancePermissionMixin, ComplianceFormMixin, generic.UpdateView):
    model = Risk
    form_class = RiskForm
    action = "change"
    list_url_name = "risk_list"
    success_message = "Risk updated."

    def get_success_url(self):
        return reverse("risk_detail", args=[self.object.pk])


class RiskDelete(ComplianceDeleteView):
    model = Risk
    success_url = reverse_lazy("risk_list")


# --------------------------------------------------------------------------
# Policies & documents
# --------------------------------------------------------------------------

class DocumentList(CompliancePermissionMixin, generic.ListView):
    model = ComplianceDocument
    template_name = "compliance/document_list.html"
    context_object_name = "documents"

    def get_queryset(self):
        documents = ComplianceDocument.objects.select_related("owner").order_by("title")
        query = self.request.GET.get("q", "").strip()
        if query:
            documents = documents.filter(title__icontains=query)
        return documents

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["today"] = timezone.localdate()
        return context


class DocumentDetail(CompliancePermissionMixin, generic.DetailView):
    model = ComplianceDocument
    template_name = "compliance/document_detail.html"
    context_object_name = "document"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["today"] = timezone.localdate()
        return context


class DocumentCreate(CompliancePermissionMixin, ComplianceFormMixin, generic.CreateView):
    model = ComplianceDocument
    form_class = ComplianceDocumentForm
    action = "add"
    list_url_name = "document_list"
    success_message = "Document added."

    def get_initial(self):
        return {"owner": self.request.user}

    def get_success_url(self):
        return reverse("document_detail", args=[self.object.pk])


class DocumentUpdate(CompliancePermissionMixin, ComplianceFormMixin, generic.UpdateView):
    model = ComplianceDocument
    form_class = ComplianceDocumentForm
    action = "change"
    list_url_name = "document_list"
    success_message = "Document updated."

    def get_success_url(self):
        return reverse("document_detail", args=[self.object.pk])


class DocumentDelete(ComplianceDeleteView):
    model = ComplianceDocument
    success_url = reverse_lazy("document_list")


# --------------------------------------------------------------------------
# Audits & controls
# --------------------------------------------------------------------------

class AuditList(CompliancePermissionMixin, generic.ListView):
    model = Audit
    template_name = "compliance/audit_list.html"
    context_object_name = "audits"

    def get_queryset(self):
        return (
            Audit.objects
            .select_related("created_by")
            .prefetch_related("controls")
            .annotate(
                failed=Count("controls", filter=Q(controls__result="failed")),
            )
            .order_by("-start_date")
        )


class AuditDetail(CompliancePermissionMixin, generic.DetailView):
    model = Audit
    template_name = "compliance/audit_detail.html"
    context_object_name = "audit"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controls = self.object.controls.prefetch_related("corrective_actions")
        context["controls"] = controls
        context["control_form"] = AuditControlForm()
        context["result_counts"] = {
            result: sum(1 for control in controls if control.result == result)
            for result, _ in AuditControl.RESULT_CHOICES
        }
        return context


class AuditCreate(CompliancePermissionMixin, ComplianceFormMixin, generic.CreateView):
    model = Audit
    form_class = AuditForm
    action = "add"
    list_url_name = "audit_list"
    success_message = "Audit created. Add the controls to assess."

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("audit_detail", args=[self.object.pk])


class AuditUpdate(CompliancePermissionMixin, ComplianceFormMixin, generic.UpdateView):
    model = Audit
    form_class = AuditForm
    action = "change"
    list_url_name = "audit_list"
    success_message = "Audit updated."

    def get_success_url(self):
        return reverse("audit_detail", args=[self.object.pk])


class AuditDelete(ComplianceDeleteView):
    model = Audit
    success_url = reverse_lazy("audit_list")


class ControlCreate(CompliancePermissionMixin, ComplianceFormMixin, generic.CreateView):
    model = AuditControl
    form_class = AuditControlForm
    action = "add"
    list_url_name = "audit_list"
    success_message = "Control added."

    def dispatch(self, request, *args, **kwargs):
        self.audit = get_object_or_404(Audit, pk=kwargs["audit_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.audit = self.audit
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("audit_detail", args=[self.audit.pk])


class ControlUpdate(CompliancePermissionMixin, ComplianceFormMixin, generic.UpdateView):
    model = AuditControl
    form_class = AuditControlForm
    action = "change"
    list_url_name = "audit_list"
    success_message = "Control updated."

    def get_success_url(self):
        return reverse("audit_detail", args=[self.object.audit_id])


class ControlDelete(ComplianceDeleteView):
    model = AuditControl

    def get_success_url(self):
        return reverse("audit_detail", args=[self.object.audit_id])


# --------------------------------------------------------------------------
# Corrective actions
# --------------------------------------------------------------------------

class ActionList(CompliancePermissionMixin, generic.ListView):
    model = CorrectiveAction
    template_name = "compliance/action_list.html"
    context_object_name = "actions"

    def get_queryset(self):
        actions = CorrectiveAction.objects.select_related(
            "owner__user",
            "source_finding__audit",
            "source_incident",
        )
        status = self.request.GET.get("status")
        if status:
            actions = actions.filter(status=status)
        return actions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status"] = self.request.GET.get("status", "")
        context["status_choices"] = CorrectiveAction.STATUS_CHOICES
        return context


class ActionDetail(CompliancePermissionMixin, generic.DetailView):
    model = CorrectiveAction
    template_name = "compliance/action_detail.html"
    context_object_name = "action"


class ActionCreate(CompliancePermissionMixin, ComplianceFormMixin, generic.CreateView):
    model = CorrectiveAction
    form_class = CorrectiveActionForm
    action = "add"
    list_url_name = "action_list"
    success_message = "Corrective action raised."

    def get_initial(self):
        """Pre-fill from a failed audit control or an incident when raised from one."""

        initial = {}

        finding = AuditControl.objects.filter(pk=self.request.GET.get("finding") or None).first()
        if finding:
            initial["source_finding"] = finding
            initial["title"] = f"Address finding: {finding.requirement[:80]}"
            initial["description"] = finding.finding

        incident = Incident.objects.filter(pk=self.request.GET.get("incident") or None).first()
        if incident:
            initial["source_incident"] = incident
            initial["title"] = f"Follow-up for incident #{incident.pk}"
            initial["description"] = incident.corrective_action
            initial["priority"] = (
                incident.severity if incident.severity in dict(CorrectiveAction.PRIORITY_CHOICES) else "medium"
            )

        return initial

    def get_success_url(self):
        return reverse("corrective_action_detail", args=[self.object.pk])


class ActionUpdate(CompliancePermissionMixin, ComplianceFormMixin, generic.UpdateView):
    model = CorrectiveAction
    form_class = CorrectiveActionForm
    action = "change"
    list_url_name = "action_list"
    success_message = "Corrective action updated."

    def get_success_url(self):
        return reverse("corrective_action_detail", args=[self.object.pk])


class ActionDelete(ComplianceDeleteView):
    model = CorrectiveAction
    success_url = reverse_lazy("action_list")
