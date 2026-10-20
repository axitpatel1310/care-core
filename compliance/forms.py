from django import forms

from .models import (
    Audit,
    AuditControl,
    ComplianceDocument,
    CorrectiveAction,
    Risk,
)


DATE_WIDGET = forms.DateInput(attrs={"type": "date"})


class ComplianceDocumentForm(forms.ModelForm):

    class Meta:
        model = ComplianceDocument

        fields = [
            "title",
            "document_type",
            "version",
            "owner",
            "status",
            "last_reviewed",
            "next_review",
            "file",
        ]

        widgets = {
            "last_reviewed": DATE_WIDGET,
            "next_review": DATE_WIDGET,
        }


class RiskForm(forms.ModelForm):

    class Meta:
        model = Risk

        fields = [
            "description",
            "category",
            "likelihood",
            "impact",
            "owner",
            "mitigation",
            "review_date",
            "status",
        ]

        widgets = {
            "review_date": DATE_WIDGET,
            "mitigation": forms.Textarea(attrs={"rows": 4}),
        }


class AuditForm(forms.ModelForm):

    class Meta:
        model = Audit

        fields = [
            "title",
            "description",
            "start_date",
            "completion_date",
            "status",
        ]

        widgets = {
            "start_date": DATE_WIDGET,
            "completion_date": DATE_WIDGET,
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class AuditControlForm(forms.ModelForm):

    class Meta:
        model = AuditControl

        fields = [
            "requirement",
            "result",
            "evidence",
            "finding",
            "notes",
        ]

        widgets = {
            "requirement": forms.Textarea(attrs={"rows": 2}),
            "evidence": forms.Textarea(attrs={"rows": 2}),
            "finding": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }


class CorrectiveActionForm(forms.ModelForm):

    class Meta:
        model = CorrectiveAction

        fields = [
            "title",
            "description",
            "owner",
            "priority",
            "due_date",
            "status",
            "source_finding",
            "source_incident",
        ]

        widgets = {
            "due_date": DATE_WIDGET,
            "description": forms.Textarea(attrs={"rows": 4}),
        }
