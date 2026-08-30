from django import forms

from .models import Incident


class IncidentForm(forms.ModelForm):

    class Meta:
        model = Incident

        fields = [
            "resident",
            "incident_date",
            "category",
            "severity",
            "description",
            "immediate_action",
            "status",
            "investigation_notes",
            "corrective_action",
        ]

        widgets = {
            "incident_date": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Describe what happened...",
                }
            ),

            "immediate_action": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "What immediate action was taken?",
                }
            ),

            "investigation_notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Investigation findings...",
                }
            ),

            "corrective_action": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Corrective or preventative action...",
                }
            ),
        }

from django import forms

from .models import Incident

class IncidentInvestigationForm(forms.ModelForm):

    class Meta:
        model = Incident

        fields = [
            "status",
            "investigation_notes",
            "corrective_action",
        ]

        widgets = {
            "status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "investigation_notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                }
            ),

            "corrective_action": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                }
            ),
        }