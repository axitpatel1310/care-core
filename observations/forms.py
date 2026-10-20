from django import forms

from .models import Observation


class ObservationForm(forms.ModelForm):

    class Meta:
        model = Observation

        fields = [
            "resident",
            "recorded_at",
            "respiratory_rate",
            "spo2",
            "spo2_scale",
            "on_oxygen",
            "systolic_bp",
            "diastolic_bp",
            "pulse",
            "consciousness",
            "temperature",
            "blood_glucose",
            "pain_score",
            "notes",
        ]

        widgets = {
            "recorded_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "temperature": forms.NumberInput(
                attrs={"step": "0.1"}
            ),
            "blood_glucose": forms.NumberInput(
                attrs={"step": "0.1"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Context, interventions or concerns...",
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        systolic = cleaned_data.get("systolic_bp")
        diastolic = cleaned_data.get("diastolic_bp")

        if systolic and diastolic and diastolic >= systolic:
            self.add_error(
                "diastolic_bp",
                "Diastolic pressure must be lower than systolic pressure.",
            )

        return cleaned_data


class ObservationAmendForm(ObservationForm):
    """Correct a recorded observation; the reason is kept with the record and the audit trail keeps the old values."""

    amendment_reason = forms.CharField(
        label="Reason for amendment",
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "e.g. Transcription error: pulse was 82, not 28."}),
        min_length=10,
    )

    class Meta(ObservationForm.Meta):
        fields = [field for field in ObservationForm.Meta.fields if field != "resident"]
