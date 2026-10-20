from django import forms
from facility.occupancy import OCCUPYING_STATUSES, occupants

from .models import Resident, ResidentContact

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

    def clean(self):

        cleaned_data = super().clean()

        room = cleaned_data.get("room")
        status = cleaned_data.get("status")

        if room:
            cleaned_data["facility"] = room.ward.facility
        elif not cleaned_data.get("facility"):
            self.add_error("facility", "Choose the facility, or a room, for this resident.")

        if room and status in OCCUPYING_STATUSES:

            taken = occupants(room, exclude=self.instance).count()

            if taken >= room.capacity:
                self.add_error(
                    "room",
                    f"Room {room} is full ({taken} of {room.capacity} beds occupied).",
                )

        admission = cleaned_data.get("admission_date")
        birth = cleaned_data.get("date_of_birth")

        if admission and birth and admission < birth:
            self.add_error("admission_date", "Admission date cannot be before the date of birth.")

        return cleaned_data

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