from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from carecore.testing import make_resident, make_user
from incidents.models import Incident

from .models import Audit, AuditControl, CorrectiveAction, Risk, severity_for_score


class RiskMatrixTests(TestCase):

    def test_severity_bands(self):
        cases = [(1, "low"), (4, "low"), (5, "medium"), (9, "medium"),
                 (10, "high"), (12, "high"), (15, "extreme"), (25, "extreme")]
        for score, expected in cases:
            with self.subTest(score=score):
                self.assertEqual(severity_for_score(score), expected)

    def test_severity_recalculated_on_save(self):
        risk = Risk.objects.create(description="Falls", category="clinical", likelihood=2, impact=2)
        self.assertEqual(risk.severity, "low")

        risk.likelihood = 5
        risk.impact = 4
        risk.save()

        self.assertEqual(risk.risk_score, 20)
        self.assertEqual(risk.severity, "extreme")


class AuditScoreTests(TestCase):

    def test_compliance_score_ignores_pending_and_half_counts_partial(self):
        audit = Audit.objects.create(title="Meds", start_date=timezone.localdate())
        self.assertIsNone(audit.compliance_score)

        for result in ("passed", "passed", "partial", "failed", "pending"):
            AuditControl.objects.create(audit=audit, requirement="Req", result=result)

        self.assertEqual(audit.compliance_score, round(2.5 / 4 * 100))


class CorrectiveActionTests(TestCase):

    def test_status_transitions_stamp_dates(self):
        action = CorrectiveAction.objects.create(title="Fix", due_date=timezone.localdate())
        self.assertIsNone(action.completed_at)

        action.status = "verified"
        action.save()
        self.assertIsNotNone(action.completed_at)
        self.assertIsNotNone(action.verified_at)

        action.status = "open"
        action.save()
        self.assertIsNone(action.completed_at)
        self.assertIsNone(action.verified_at)

    def test_is_overdue(self):
        action = CorrectiveAction.objects.create(
            title="Late", due_date=timezone.localdate() - timedelta(days=1),
        )
        self.assertTrue(action.is_overdue)

        action.status = "completed"
        self.assertFalse(action.is_overdue)


class ComplianceViewTests(TestCase):

    def test_manager_can_add_risk(self):
        self.client.force_login(make_user("manager"))

        response = self.client.post(reverse("risk_create"), {
            "description": "Night staffing",
            "category": "staff",
            "likelihood": 4,
            "impact": 3,
            "status": "open",
        })

        risk = Risk.objects.get()
        self.assertRedirects(response, reverse("risk_detail", args=[risk.pk]))
        self.assertEqual(risk.severity, "high")

    def test_rn_cannot_delete_risk(self):
        risk = Risk.objects.create(description="R", category="other")
        self.client.force_login(make_user("rn"))

        response = self.client.post(reverse("risk_delete", args=[risk.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Risk.objects.exists())

    def test_action_prefilled_from_incident(self):
        incident = Incident.objects.create(
            resident=make_resident(),
            incident_date=timezone.now(),
            category="fall",
            severity="high",
            description="Fall",
            corrective_action="Review footwear",
        )
        self.client.force_login(make_user("manager"))

        response = self.client.get(reverse("action_create") + f"?incident={incident.pk}")

        form = response.context["form"]
        self.assertEqual(form.initial["source_incident"], incident)
        self.assertEqual(form.initial["priority"], "high")
        self.assertEqual(form.initial["description"], "Review footwear")

    def test_dashboard_heat_map_counts_open_risks(self):
        Risk.objects.create(description="A", category="other", likelihood=5, impact=5)
        Risk.objects.create(description="B", category="other", likelihood=5, impact=5, status="resolved")
        self.client.force_login(make_user("manager"))

        response = self.client.get(reverse("compliance_dashboard"))

        top_row = response.context["risk_matrix"][0]
        self.assertEqual(top_row["impact"], 5)
        self.assertEqual(top_row["cells"][4]["count"], 1)
