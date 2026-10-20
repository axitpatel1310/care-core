from django import forms

from .models import Medication, MedicationAdministration, MedicationDoseTime
from .schedule import default_times_for_frequency, parse_dose_times


class MedicationForm(forms.ModelForm):

    dose_times = forms.CharField(
        required=False,
        label="Dose times",
        help_text=(
            "24-hour times separated by commas, e.g. 08:00, 20:00. "
            "Left blank, times are suggested from the frequency."
        ),
        widget=forms.TextInput(attrs={"placeholder": "08:00, 20:00"}),
    )

    class Meta:
        model = Medication

        fields = [
            "resident",
            "name",
            "dose",
            "route",
            "frequency",
            "as_required",
            "dose_times",
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

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.initial["dose_times"] = ", ".join(
                dose.time.strftime("%H:%M")
                for dose in self.instance.dose_times.all()
            )

    def clean(self):

        cleaned_data = super().clean()

        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")

        if start and end and end < start:
            self.add_error("end_date", "End date cannot be before the start date.")

        if cleaned_data.get("as_required"):
            cleaned_data["parsed_times"] = []
            return cleaned_data

        raw = cleaned_data.get("dose_times", "")

        try:
            times = parse_dose_times(raw)
        except ValueError as error:
            self.add_error("dose_times", str(error))
            return cleaned_data

        if not times:
            suggested = default_times_for_frequency(cleaned_data.get("frequency"))

            if suggested is None:
                cleaned_data["as_required"] = True
                cleaned_data["parsed_times"] = []
                return cleaned_data

            times = parse_dose_times(", ".join(suggested))

        if not times:
            self.add_error(
                "dose_times",
                "Enter at least one dose time, or tick PRN for as-required medicines.",
            )

        cleaned_data["parsed_times"] = times

        return cleaned_data

    def save(self, commit=True):

        medication = super().save(commit=False)
        medication.as_required = self.cleaned_data.get("as_required", False)

        if commit:
            medication.save()
            self.save_dose_times(medication)

        return medication

    def save_dose_times(self, medication):

        times = self.cleaned_data.get("parsed_times", [])

        medication.dose_times.exclude(time__in=times).delete()

        for value in times:
            MedicationDoseTime.objects.get_or_create(
                medication=medication,
                time=value,
            )


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
                },
                format="%Y-%m-%dT%H:%M",
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

    def __init__(self, *args, scheduled_for=None, **kwargs):

        self.scheduled_for = scheduled_for

        super().__init__(*args, **kwargs)

    def clean(self):

        cleaned_data = super().clean()

        if cleaned_data.get("status") in ("refused", "withheld", "missed") and not cleaned_data.get("notes"):
            self.add_error(
                "notes",
                "Record the reason when a dose is not given.",
            )

        if self.scheduled_for is not None:

            duplicate = MedicationAdministration.objects.filter(
                medication=self.instance.medication,
                scheduled_for=self.scheduled_for,
            ).exclude(pk=self.instance.pk)

            if duplicate.exists():
                raise forms.ValidationError(
                    "This scheduled dose has already been recorded."
                )

        return cleaned_data
