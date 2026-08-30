from django import forms

from .models import Medication,MedicationAdministration

from django import forms

from .models import Medication, MedicationAdministration


class MedicationForm(forms.ModelForm):

    class Meta:
        model = Medication

        fields = [
            "resident",
            "name",
            "dose",
            "route",
            "frequency",
            "start_date",
            "end_date",
            "prescriber",
            "status",
        ]

        widgets = {
            "start_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }


class MedicationAdministrationForm(
    forms.ModelForm
):

    class Meta:
        model = MedicationAdministration

        fields = [
            "administered_at",
            "status",
            "notes",
        ]

        widgets = {
            "administered_at": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local"
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Optional administration notes..."
                    ),
                }
            ),
        }
      