from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from care.models import CarePlan, CareTask
from carecore.testing import NORMAL_VITALS, make_resident, make_user
from incidents.models import Incident
from medications.models import Medication, MedicationAdministration
from observations.models import Observation

from . import analytics
from .alerts import CRITICAL, WARNING, alerts_for
from .risk import BAND_HIGH, BAND_LOW, BAND_MODERATE, assess_resident, band_for_score
from .views import _safe_cell


class RiskScoreTests(TestCase):

    def setUp(self):
        self.now = timezone.now()
        self.resident = make_resident()
        CarePlan.objects.create(resident=self.resident, status="active")

    def test_band_thresholds(self):
        self.assertEqual(band_for_score(0), BAND_LOW)
        self.assertEqual(band_for_score(29), BAND_LOW)
        self.assertEqual(band_for_score(30), BAND_MODERATE)
        self.assertEqual(band_for_score(59), BAND_MODERATE)
        self.assertEqual(band_for_score(60), BAND_HIGH)

    def test_well_resident_scores_zero(self):
        risk = assess_resident(self.resident, now=self.now)
        self.assertEqual(risk.score, 0)
        self.assertEqual(risk.factors, [])

    def test_missing_care_plan_is_a_factor(self):
        resident = make_resident(first_name="Bob")
        risk = assess_resident(resident, now=self.now)
        self.assertEqual(risk.score, 5)
        self.assertEqual(risk.factors[0].label, "Care plan")

    def test_factors_combine_and_are_explained(self):
        self.resident.care_level = "complex"
        self.resident.save()

        Observation.objects.create(
            resident=self.resident,
            recorded_at=self.now - timedelta(hours=2),
            **{**NORMAL_VITALS, "respiratory_rate": 25, "spo2": 90, "pulse": 135},
        )

        for days in (5, 20, 40):
            Incident.objects.create(
                resident=self.resident,
                incident_date=self.now - timedelta(days=days),
                category="fall",
                severity="low",
                description="Fall",
            )

        risk = assess_resident(self.resident, now=self.now)
        points = {factor.label: factor.points for factor in risk.factors}

        self.assertEqual(points["Early warning score"], 30)
        self.assertEqual(points["Falls history"], 25)  # 3 falls capped at 25
        self.assertEqual(points["Care complexity"], 10)
        self.assertEqual(risk.score, 65)
        self.assertEqual(risk.band, BAND_HIGH)
        self.assertEqual(risk.factors[0].label, "Early warning score")

    def test_old_observations_and_falls_are_ignored(self):
        Observation.objects.create(
            resident=self.resident,
            recorded_at=self.now - timedelta(days=5),
            **{**NORMAL_VITALS, "consciousness": "U"},
        )
        Incident.objects.create(
            resident=self.resident,
            incident_date=self.now - timedelta(days=200),
            category="fall",
            severity="low",
            description="Old fall",
        )

        self.assertEqual(assess_resident(self.resident, now=self.now).score, 0)

    def test_medication_adherence_points_scale_with_missed_doses(self):
        medication = Medication.objects.create(
            resident=self.resident, name="Med", dose="1", route="Oral",
            frequency="Daily", start_date=timezone.localdate(),
        )
        for index in range(4):
            MedicationAdministration.objects.create(
                medication=medication,
                administered_at=self.now - timedelta(days=index),
                status="missed" if index < 2 else "administered",
            )

        risk = assess_resident(self.resident, now=self.now)
        self.assertEqual(risk.factors[0].label, "Medication adherence")
        self.assertEqual(risk.factors[0].points, 10)


class AlertEngineTests(TestCase):

    def setUp(self):
        cache.clear()
        self.resident = make_resident()

    def test_high_news2_raises_critical_deterioration_alert(self):
        Observation.objects.create(
            resident=self.resident,
            **{**NORMAL_VITALS, "respiratory_rate": 25, "spo2": 90, "pulse": 135},
        )

        alerts = alerts_for(make_user("rn"))
        deterioration = [alert for alert in alerts if alert.category == "Deterioration"]

        self.assertEqual(len(deterioration), 1)
        self.assertEqual(deterioration[0].severity, CRITICAL)
        self.assertEqual(alerts[0].severity, CRITICAL, "critical alerts sort first")

    def test_repeat_observations_overdue(self):
        Observation.objects.create(
            resident=self.resident,
            recorded_at=timezone.now() - timedelta(hours=3),
            **{**NORMAL_VITALS, "consciousness": "C"},
        )

        titles = [alert.title for alert in alerts_for(make_user("rn"))]

        self.assertIn(f"{self.resident}: repeat observations overdue", titles)

    def test_overdue_task_alert(self):
        CareTask.objects.create(
            resident=self.resident,
            title="Weigh resident",
            due_date=timezone.localdate() - timedelta(days=1),
        )

        alerts = alerts_for(make_user("care_worker"))

        self.assertTrue(any(
            alert.category == "Care tasks" and alert.severity == WARNING
            for alert in alerts
        ))

    def test_alerts_respect_permissions(self):
        CarePlan.objects.create(
            resident=self.resident,
            status="active",
            next_review=timezone.localdate() - timedelta(days=3),
        )

        user_without_roles = make_user(role="unknown")

        self.assertEqual(alerts_for(user_without_roles), [])
        self.assertTrue(alerts_for(make_user("care_worker")))

    def test_bell_shows_alert_count(self):
        CareTask.objects.create(
            resident=self.resident,
            title="Overdue",
            due_date=timezone.localdate() - timedelta(days=2),
        )
        self.client.force_login(make_user("care_worker"))

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.context["alert_summary"]["total"], 1)
        self.assertContains(response, 'class="notification-count')


class AnalyticsTests(TestCase):

    def setUp(self):
        self.start, self.end = analytics.period_bounds(30)
        self.resident = make_resident(
            admission_date=timezone.localdate() - timedelta(days=365),
        )

    def test_falls_rate_per_thousand_bed_days(self):
        Incident.objects.create(
            resident=self.resident,
            incident_date=timezone.now() - timedelta(days=1),
            category="fall",
            severity="low",
            description="Fall",
        )

        kpis = analytics.kpis(self.start, self.end)

        self.assertEqual(kpis["bed_days"], 30)
        self.assertEqual(kpis["falls"], 1)
        self.assertEqual(kpis["falls_rate"], round(1 / 30 * 1000, 2))

    def test_medication_adherence(self):
        medication = Medication.objects.create(
            resident=self.resident, name="Med", dose="1", route="Oral",
            frequency="Daily", start_date=timezone.localdate(),
        )
        for status in ("administered", "administered", "administered", "refused"):
            MedicationAdministration.objects.create(
                medication=medication,
                administered_at=timezone.now() - timedelta(days=1),
                status=status,
            )

        self.assertEqual(analytics.kpis(self.start, self.end)["medication_adherence"], 75.0)

    def test_no_data_returns_none_not_zero_division(self):
        kpis = analytics.kpis(self.start, self.end)
        self.assertIsNone(kpis["medication_adherence"])
        self.assertIsNone(kpis["task_on_time_rate"])
        self.assertIsNone(kpis["mean_resolution_hours"])

    def test_incidents_by_month_covers_every_month(self):
        start, end = analytics.period_bounds(180)
        data = analytics.incidents_by_month(start, end)
        self.assertGreaterEqual(len(data["labels"]), 6)
        self.assertEqual(set(data["series"]), {"Low", "Medium", "High", "Critical"})


class InsightsViewTests(TestCase):

    def setUp(self):
        self.resident = make_resident()
        Incident.objects.create(
            resident=self.resident,
            incident_date=timezone.now() - timedelta(days=1),
            category="other",
            severity="low",
            description="=HYPERLINK(\"http://evil.test\")",
        )

    def test_care_worker_cannot_open_analytics(self):
        self.client.force_login(make_user("care_worker"))
        self.assertEqual(self.client.get(reverse("analytics_dashboard")).status_code, 403)

    def test_manager_sees_analytics(self):
        self.client.force_login(make_user("manager"))
        response = self.client.get(reverse("analytics_dashboard") + "?days=365")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["days"], 365)

    def test_csv_export_escapes_formulas_and_is_audited(self):
        manager = make_user("manager")
        self.client.force_login(manager)

        response = self.client.get(reverse("analytics_export", args=["incidents"]))

        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode()
        self.assertIn("'=HYPERLINK", content)
        self.assertTrue(manager.audit_logs.filter(module="insights").exists())

    def test_unknown_export_is_404(self):
        self.client.force_login(make_user("manager"))
        response = self.client.get(reverse("analytics_export", args=["passwords"]))
        self.assertEqual(response.status_code, 404)

    def test_safe_cell_keeps_negative_numbers(self):
        self.assertEqual(_safe_cell("-5"), "-5")
        self.assertEqual(_safe_cell("+cmd"), "'+cmd")
        self.assertEqual(_safe_cell(None), "")

    def test_handover_and_risk_register_render(self):
        self.client.force_login(make_user("care_worker"))

        handover = self.client.get(reverse("shift_handover") + "?hours=24")
        register = self.client.get(reverse("resident_risk_register"))

        self.assertContains(handover, str(self.resident))
        self.assertContains(register, str(self.resident))


class RiskQueryCountTests(TestCase):
    """The register must not issue queries per resident."""

    def test_query_count_is_independent_of_resident_count(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from .risk import assess_residents

        def queries_for(count):
            residents = [make_resident(first_name=f"R{count}-{i}") for i in range(count)]
            with CaptureQueriesContext(connection) as captured:
                assess_residents(residents)
            return len(captured)

        self.assertEqual(queries_for(1), queries_for(8))
