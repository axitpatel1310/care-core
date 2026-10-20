from datetime import time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from carecore.testing import (
    make_resident,
    make_staff,
    make_user,
)
from insights.alerts import alerts_for

from .forms import MedicationForm
from .models import (
    Medication,
    MedicationAdministration,
    MedicationDoseTime,
)
from .schedule import (
    default_times_for_frequency,
    dose_state,
    doses_for_day,
    parse_dose_times,
    scheduled_datetime,
)


class ScheduleParsingTests(TestCase):

    def test_frequency_suggestions(self):
        self.assertEqual(default_times_for_frequency("Twice daily"), ["08:00", "20:00"])
        self.assertEqual(default_times_for_frequency("TDS"), ["08:00", "14:00", "20:00"])
        self.assertEqual(default_times_for_frequency("Once daily at night"), ["21:00"])
        self.assertIsNone(default_times_for_frequency("PRN for pain"))
        self.assertEqual(default_times_for_frequency("Every 6 hours"), [])

    def test_parse_dose_times(self):
        self.assertEqual(
            parse_dose_times("20:00, 8:00; 0830 20:00"),
            [time(8, 0), time(8, 30), time(20, 0)],
        )
        with self.assertRaises(ValueError):
            parse_dose_times("25:00")

    def test_dose_state_windows(self):
        due = timezone.now()
        self.assertEqual(dose_state(due, None, due - timedelta(hours=2)), "upcoming")
        self.assertEqual(dose_state(due, None, due - timedelta(minutes=30)), "due")
        self.assertEqual(dose_state(due, None, due + timedelta(minutes=59)), "due")
        self.assertEqual(dose_state(due, None, due + timedelta(minutes=61)), "overdue")


class MedicationScheduleTests(TestCase):

    def setUp(self):
        self.resident = make_resident()
        self.today = timezone.localdate()
        self.medication = Medication.objects.create(
            resident=self.resident, name="Metformin", dose="500 mg", route="Oral",
            frequency="Twice daily", start_date=self.today - timedelta(days=10),
        )
        for value in (time(8, 0), time(20, 0)):
            MedicationDoseTime.objects.create(medication=self.medication, time=value)

        self.rn = make_user("rn")
        make_staff(self.rn)

    def test_form_suggests_times_from_frequency(self):
        form = MedicationForm(data={
            "resident": self.resident.pk, "name": "Amlodipine", "dose": "5 mg", "route": "Oral",
            "frequency": "Three times daily", "start_date": self.today.isoformat(), "status": "active",
        })
        self.assertTrue(form.is_valid(), form.errors)

        medication = form.save()

        self.assertEqual(medication.schedule_display, "08:00, 14:00, 20:00")

    def test_form_prn_has_no_dose_times(self):
        form = MedicationForm(data={
            "resident": self.resident.pk, "name": "Paracetamol", "dose": "1 g", "route": "Oral",
            "frequency": "As required", "start_date": self.today.isoformat(), "status": "active",
        })
        self.assertTrue(form.is_valid(), form.errors)

        medication = form.save()

        self.assertTrue(medication.as_required)
        self.assertFalse(medication.dose_times.exists())
        self.assertEqual(doses_for_day(self.today, Medication.objects.filter(pk=medication.pk)), [])

    def test_doses_match_recorded_administrations(self):
        morning = scheduled_datetime(self.today, time(8, 0))
        MedicationAdministration.objects.create(
            medication=self.medication, administered_at=morning, scheduled_for=morning, status="refused",
        )

        doses = doses_for_day(self.today, now=scheduled_datetime(self.today, time(23, 0)))

        self.assertEqual([dose.state for dose in doses], ["refused", "overdue"])

    def test_record_scheduled_dose_links_it(self):
        self.client.force_login(self.rn)
        evening = scheduled_datetime(self.today, time(20, 0))
        url = reverse("administration_create", args=[self.medication.pk]) + f"?scheduled_for={evening.isoformat()}"

        self.client.post(url, {
            "administered_at": timezone.localtime(evening).strftime("%Y-%m-%dT%H:%M"),
            "status": "administered",
            "scheduled_for": evening.isoformat(),
        })

        record = MedicationAdministration.objects.get()
        self.assertEqual(record.scheduled_for, evening)
        self.assertEqual(record.administered_by, self.rn.staff_profile)

        # The same dose cannot be recorded twice.
        response = self.client.post(url, {
            "administered_at": timezone.localtime(evening).strftime("%Y-%m-%dT%H:%M"),
            "status": "administered",
            "scheduled_for": evening.isoformat(),
        })
        self.assertContains(response, "already been recorded")
        self.assertEqual(MedicationAdministration.objects.count(), 1)

    def test_dose_not_on_schedule_is_rejected(self):
        self.client.force_login(self.rn)
        bogus = scheduled_datetime(self.today, time(13, 0))

        response = self.client.get(
            reverse("administration_create", args=[self.medication.pk]) + f"?scheduled_for={bogus.isoformat()}"
        )

        self.assertEqual(response.status_code, 404)

    def test_refusal_requires_a_reason(self):
        self.client.force_login(self.rn)

        response = self.client.post(reverse("administration_create", args=[self.medication.pk]), {
            "administered_at": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
            "status": "refused",
        })

        self.assertContains(response, "Record the reason")
        self.assertFalse(MedicationAdministration.objects.exists())

    def test_overdue_dose_raises_alert(self):
        late = scheduled_datetime(self.today, time(8, 0)) + timedelta(hours=3)

        titles = [alert.title for alert in alerts_for(self.rn, now=late)]

        self.assertIn("Dose overdue: Metformin", titles)

    def test_round_and_mar_render(self):
        self.client.force_login(self.rn)

        round_page = self.client.get(reverse("medication_due_today"))
        mar = self.client.get(reverse("resident_mar", args=[self.resident.pk]))

        self.assertContains(round_page, "Metformin")
        self.assertEqual(len(mar.context["rows"]), 2)
        self.assertEqual(len(mar.context["rows"][0]["cells"]), 7)
