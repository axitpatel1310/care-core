from django import forms

from .models import Incident


class IncidentForm(forms.ModelForm):

    class Meta:
        model = Incident

        fields = [
            "resident",
            "facility",
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

    def clean(self):

        cleaned_data = super().clean()

        resident = cleaned_data.get("resident")

        if resident and resident.facility_id:
            cleaned_data["facility"] = resident.facility
        elif not cleaned_data.get("facility"):
            self.add_error("facility", "Choose the facility where this happened.")

        return cleaned_data


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