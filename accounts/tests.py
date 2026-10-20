from django.contrib.auth import authenticate
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from carecore.testing import make_resident, make_user
from residents.models import Resident

from .models import AuditLog


class RoleGroupTests(TestCase):

    def test_new_user_gets_role_group_permissions(self):
        user = make_user("care_worker")

        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["Personal Care Worker"])
        self.assertTrue(user.has_perm("residents.view_resident"))
        self.assertFalse(user.has_perm("residents.add_resident"))

    def test_changing_role_swaps_group(self):
        user = make_user("care_worker")

        user.role = "manager"
        user.save()
        user = type(user).objects.get(pk=user.pk)  # clear permission cache

        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["Manager"])
        self.assertTrue(user.has_perm("residents.add_resident"))
        self.assertTrue(user.has_perm("compliance.add_risk"))

    def test_admin_role_has_every_permission(self):
        self.assertTrue(make_user("admin").has_perm("observations.delete_observation"))


class EmailLoginTests(TestCase):

    def test_login_with_email_is_case_insensitive(self):
        user = make_user("rn", email="nurse@example.test")
        user.username = "nurse_username"
        user.save()

        self.assertEqual(authenticate(username="NURSE@example.test", password="Test-password-123"), user)
        self.assertIsNone(authenticate(username="nurse@example.test", password="wrong"))

    def test_login_view_signs_in_and_is_audited(self):
        make_user("rn", email="nurse@example.test")

        response = self.client.post(
            reverse("login"),
            {"email": "nurse@example.test", "password": "Test-password-123"},
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(AuditLog.objects.filter(action="login").exists())

    def test_failed_login_is_audited(self):
        self.client.post(reverse("login"), {"email": "nobody@example.test", "password": "x"})

        self.assertTrue(AuditLog.objects.filter(action="login_failed").exists())


class AuditTrailTests(TestCase):

    def setUp(self):
        self.manager = make_user("manager")
        self.client.force_login(self.manager)

    def test_create_update_delete_are_logged_with_user_and_diff(self):
        resident = make_resident()
        resident.care_level = "complex"
        resident.save()
        resident.delete()

        logs = AuditLog.objects.filter(object_type="Resident").order_by("timestamp", "pk")
        self.assertEqual([log.action for log in logs], ["create", "update", "delete"])
        self.assertEqual(logs[1].changes, {"care_level": ["standard", "complex"]})

    def test_view_changes_record_the_acting_user_and_ip(self):
        resident = make_resident()

        self.client.post(reverse("resident_edit", args=[resident.pk]), {
            "first_name": "Ada",
            "last_name": "Byron",
            "date_of_birth": "1940-01-01",
            "gender": "female",
            "admission_date": timezone.localdate().isoformat(),
            "status": "active",
            "care_level": "standard",
        })

        self.assertEqual(Resident.objects.get().last_name, "Byron")
        log = AuditLog.objects.get(action="update", object_type="Resident")
        self.assertEqual(log.user, self.manager)
        self.assertEqual(log.ip_address, "127.0.0.1")
        self.assertEqual(log.changes["last_name"], ["Lovelace", "Byron"])

    def test_unchanged_save_is_not_logged(self):
        resident = make_resident()
        resident.save()

        self.assertFalse(AuditLog.objects.filter(action="update").exists())

    def test_audit_log_page_is_admin_only_and_filterable(self):
        make_resident()

        self.assertRedirects(self.client.get(reverse("audit_log")), reverse("dashboard"))

        self.client.force_login(make_user("admin"))
        response = self.client.get(reverse("audit_log") + "?action=create&module=residents")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(log.action == "create" for log in response.context["logs"]))
