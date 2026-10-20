from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from care.models import CareTask
from carecore.testing import NORMAL_VITALS, make_resident, make_staff, make_user
from staff.models import ResidentStaffAssignment

from . import news2
from .models import Observation
from .services import escalate_if_required


class News2ParameterScoringTests(TestCase):
    """Boundary values taken from the RCP NEWS2 chart."""

    def assertBands(self, func, cases):
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(func(value), expected)

    def test_respiratory_rate(self):
        self.assertBands(news2.score_respiratory_rate, [
            (8, 3), (9, 1), (11, 1), (12, 0), (20, 0), (21, 2), (24, 2), (25, 3),
        ])

    def test_spo2_scale_1(self):
        self.assertBands(news2.score_spo2_scale_1, [
            (91, 3), (92, 2), (93, 2), (94, 1), (95, 1), (96, 0), (100, 0),
        ])

    def test_spo2_scale_2_on_air(self):
        self.assertBands(lambda v: news2.score_spo2_scale_2(v, on_oxygen=False), [
            (83, 3), (84, 2), (85, 2), (86, 1), (87, 1), (88, 0), (92, 0), (93, 0), (99, 0),
        ])

    def test_spo2_scale_2_on_oxygen_penalises_over_oxygenation(self):
        self.assertBands(lambda v: news2.score_spo2_scale_2(v, on_oxygen=True), [
            (92, 0), (93, 1), (94, 1), (95, 2), (96, 2), (97, 3),
        ])

    def test_systolic_bp(self):
        self.assertBands(news2.score_systolic_bp, [
            (90, 3), (91, 2), (100, 2), (101, 1), (110, 1), (111, 0), (219, 0), (220, 3),
        ])

    def test_pulse(self):
        self.assertBands(news2.score_pulse, [
            (40, 3), (41, 1), (50, 1), (51, 0), (90, 0), (91, 1), (110, 1), (111, 2), (130, 2), (131, 3),
        ])

    def test_temperature(self):
        self.assertBands(news2.score_temperature, [
            (Decimal("35.0"), 3), (Decimal("35.1"), 1), (Decimal("36.0"), 1), (Decimal("36.1"), 0),
            (Decimal("38.0"), 0), (Decimal("38.1"), 1), (Decimal("39.0"), 1), (Decimal("39.1"), 2),
        ])

    def test_consciousness(self):
        self.assertEqual(news2.score_consciousness("A"), 0)
        for level in "CVPU":
            self.assertEqual(news2.score_consciousness(level), 3)

    def test_oxygen(self):
        self.assertEqual(news2.score_air_or_oxygen(False), 0)
        self.assertEqual(news2.score_air_or_oxygen(True), 2)


class News2AggregateTests(TestCase):

    def calc(self, **overrides):
        vitals = {**NORMAL_VITALS, **overrides}
        return news2.calculate_news2(**vitals)

    def test_normal_observations_score_zero_low_risk(self):
        result = self.calc()
        self.assertEqual(result.total, 0)
        self.assertEqual(result.risk_level, news2.RISK_LOW)
        self.assertFalse(result.requires_escalation)
        self.assertEqual(result.monitoring_hours, 12)

    def test_single_red_parameter_is_low_medium(self):
        result = self.calc(consciousness="C")
        self.assertEqual(result.total, 3)
        self.assertTrue(result.has_red_score)
        self.assertEqual(result.risk_level, news2.RISK_LOW_MEDIUM)
        self.assertTrue(result.requires_escalation)

    def test_aggregate_five_is_medium(self):
        # RR 22 (2) + pulse 115 (2) + temp 38.5 (1) = 5
        result = self.calc(respiratory_rate=22, pulse=115, temperature="38.5")
        self.assertEqual(result.total, 5)
        self.assertEqual(result.risk_level, news2.RISK_MEDIUM)

    def test_aggregate_seven_is_high(self):
        # RR 25 (3) + SpO2 93 (2) + on O2 (2) = 7
        result = self.calc(respiratory_rate=25, spo2=93, on_oxygen=True)
        self.assertEqual(result.total, 7)
        self.assertEqual(result.risk_level, news2.RISK_HIGH)
        self.assertEqual(result.monitoring_hours, 0)

    def test_scale_2_used_when_selected(self):
        scale_1 = self.calc(spo2=89)
        scale_2 = self.calc(spo2=89, spo2_scale=2)
        self.assertEqual(scale_1.breakdown["spo2"], 3)
        self.assertEqual(scale_2.breakdown["spo2"], 0)


class ObservationModelTests(TestCase):

    def setUp(self):
        self.resident = make_resident()

    def test_save_stores_calculated_score(self):
        obs = Observation.objects.create(resident=self.resident, **{**NORMAL_VITALS, "pulse": 120})
        self.assertEqual(obs.news2_score, 2)
        self.assertEqual(obs.risk_level, news2.RISK_LOW)

        obs.consciousness = "V"
        obs.save()
        obs.refresh_from_db()
        self.assertEqual(obs.news2_score, 5)
        self.assertEqual(obs.risk_level, news2.RISK_MEDIUM)

    def test_escalation_creates_one_urgent_task_for_assigned_nurse(self):
        nurse = make_staff(make_user("rn"))
        ResidentStaffAssignment.objects.create(
            staff=nurse, resident=self.resident, role="nurse", start_date="2025-01-01",
        )

        obs = Observation.objects.create(
            resident=self.resident,
            **{**NORMAL_VITALS, "respiratory_rate": 25, "spo2": 90, "pulse": 135},
        )

        task = escalate_if_required(obs)

        self.assertIsNotNone(task)
        self.assertEqual(task.priority, "urgent")
        self.assertEqual(task.assigned_to, nurse)
        self.assertEqual(task.task_type, "health_check")
        self.assertIsNone(escalate_if_required(obs), "should not escalate twice")
        self.assertEqual(CareTask.objects.count(), 1)

    def test_low_risk_does_not_escalate(self):
        obs = Observation.objects.create(resident=self.resident, **NORMAL_VITALS)
        self.assertIsNone(escalate_if_required(obs))


class ObservationViewTests(TestCase):

    def setUp(self):
        self.resident = make_resident()
        self.carer = make_user("care_worker")
        make_staff(self.carer)

    def post_data(self, **overrides):
        data = {
            **NORMAL_VITALS,
            "resident": self.resident.pk,
            "recorded_at": "2026-01-01T10:00",
            "spo2_scale": 1,
            **overrides,
        }
        if not data["on_oxygen"]:
            data.pop("on_oxygen")
        return data

    def test_care_worker_can_record_and_high_score_escalates(self):
        self.client.force_login(self.carer)

        response = self.client.post(
            reverse("observation_create"),
            self.post_data(respiratory_rate=26, consciousness="V"),
        )

        obs = Observation.objects.get()
        self.assertRedirects(response, reverse("observation_detail", args=[obs.pk]))
        self.assertEqual(obs.recorded_by, self.carer.staff_profile)
        self.assertEqual(obs.news2_score, 6)
        self.assertIsNotNone(obs.escalation_task)

    def test_diastolic_must_be_below_systolic(self):
        self.client.force_login(self.carer)

        response = self.client.post(
            reverse("observation_create"),
            self.post_data(diastolic_bp=130),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Observation.objects.exists())

    def test_care_worker_cannot_delete(self):
        obs = Observation.objects.create(resident=self.resident, **NORMAL_VITALS)
        self.client.force_login(self.carer)

        response = self.client.post(reverse("observation_delete", args=[obs.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Observation.objects.exists())

    def test_resident_chart_renders(self):
        Observation.objects.create(resident=self.resident, **NORMAL_VITALS)
        self.client.force_login(self.carer)

        response = self.client.get(reverse("resident_observations", args=[self.resident.pk]))

        self.assertContains(response, "news2Chart")
