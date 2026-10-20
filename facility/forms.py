from django import forms

from .models import Facility, Ward, Room


class FacilityForm(forms.ModelForm):

    class Meta:
        model = Facility
        fields = [
            "name",
            "address",
            "phone",
            "email",
            "manager",
            "status",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Main Facility",
                }
            ),

            "address": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Facility address",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "placeholder": "+61 ...",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "placeholder": "facility@example.com",
                }
            ),
        }


class WardForm(forms.ModelForm):

    class Meta:
        model = Ward
        fields = [
            "facility",
            "name",
            "description",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Wing A",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),
        }


class RoomForm(forms.ModelForm):

    class Meta:
        model = Room
        fields = [
            "ward",
            "room_number",
            "capacity",
        ]

        widgets = {
            "room_number": forms.TextInput(
                attrs={
                    "placeholder": "101",
                }
            ),
        }

    def clean_capacity(self):

        capacity = self.cleaned_data["capacity"]

        if self.instance.pk:

            from .occupancy import occupants

            current = occupants(self.instance).count()

            if capacity < current:
                raise forms.ValidationError(
                    f"{current} residents currently occupy this room; "
                    "move residents before reducing capacity."
                )

        if capacity < 1:
            raise forms.ValidationError("A room must hold at least one resident.")

        return capacity
