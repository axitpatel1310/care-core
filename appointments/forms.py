from django import forms

from .models import Appointment


class AppointmentForm(forms.ModelForm):

    class Meta:
        model = Appointment

        fields = [
            "resident",
            "assigned_staff",
            "title",
            "appointment_type",
            "appointment_date",
            "start_time",
            "end_time",
            "location",
            "provider",
            "status",
            "notes",
            "outcome",
        ]

        widgets = {
            "appointment_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),

            "start_time": forms.TimeInput(
                attrs={
                    "type": "time",
                }
            ),

            "end_time": forms.TimeInput(
                attrs={
                    "type": "time",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Appointment notes...",
                }
            ),

            "outcome": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Record the appointment outcome...",
                }
            ),
        }