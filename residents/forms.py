from django import forms
from .models import Resident,ResidentContact

class ResidentForm(forms.ModelForm):

    class Meta:
        model = Resident

        fields = [
            field.name
            for field in Resident._meta.fields
            if field.name not in ["id", "created_at", "updated_at"]
        ]

        widgets = {
            "date_of_birth": forms.DateInput(
                attrs={"type": "date"}
            ),

            "admission_date": forms.DateInput(
                attrs={"type": "date"}
            ),

            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Additional resident notes...",
                }
            ),
        }

class ResidentContactForm(forms.ModelForm):

    class Meta:
        model = ResidentContact

        fields = [
            "contact_type",
            "name",
            "relationship",
            "phone",
            "email",
            "address",
        ]

        widgets = {
            "address": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Full address...",
                }
            ),
        }