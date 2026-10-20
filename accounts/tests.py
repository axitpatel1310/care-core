import re

from django.contrib.auth import authenticate
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from carecore.testing import make_resident, make_user
from residents.models import Resident

from .models import AuditLog, User


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


class LoginSecurityTests(TestCase):

    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.user = make_user("rn", email="nurse@example.test")

    def login(self, password="Test-password-123", next_url=None, email="nurse@example.test"):
        url = reverse("login") + (f"?next={next_url}" if next_url else "")
        return self.client.post(url, {"email": email, "password": password})

    def test_external_next_url_is_ignored(self):
        response = self.login(next_url="https://evil.example.com/phish")
        self.assertRedirects(response, reverse("dashboard"))

    def test_protocol_relative_next_url_is_ignored(self):
        response = self.login(next_url="//evil.example.com/")
        self.assertRedirects(response, reverse("dashboard"))

    def test_internal_next_url_is_followed(self):
        response = self.login(next_url="/residents/")
        self.assertRedirects(response, "/residents/")

    def test_repeated_failures_lock_out_sign_in(self):
        from . import throttle

        for _ in range(throttle.MAX_FAILURES_PER_EMAIL):
            self.login(password="wrong")

        response = self.login()  # correct password, but locked

        self.assertEqual(response.status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTrue(AuditLog.objects.filter(description__icontains="throttling").exists())

    def test_successful_login_resets_failure_count(self):
        from . import throttle

        for _ in range(throttle.MAX_FAILURES_PER_EMAIL - 1):
            self.login(password="wrong")

        self.login()
        self.client.logout()

        for _ in range(throttle.MAX_FAILURES_PER_EMAIL - 1):
            self.login(password="wrong")

        self.assertRedirects(self.login(), reverse("dashboard"))

    def test_logout_requires_post(self):
        self.client.force_login(self.user)

        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

        self.client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", self.client.session)


class RegistrationApprovalTests(TestCase):

    def register(self, **overrides):
        data = {
            "first_name": "New",
            "last_name": "Starter",
            "email": "new.starter@example.test",
            "password": "a-Strong-passphrase-42",
            "confirm_password": "a-Strong-passphrase-42",
            **overrides,
        }
        return self.client.post(reverse("register"), data)

    def test_registration_creates_inactive_account_that_cannot_sign_in(self):
        self.register()

        user = User.objects.get(email="new.starter@example.test")
        self.assertFalse(user.is_active)

        response = self.client.post(
            reverse("login"),
            {"email": "new.starter@example.test", "password": "a-Strong-passphrase-42"},
        )

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "awaiting approval")

    def test_weak_password_rejected(self):
        self.register(password="password", confirm_password="password")
        self.assertFalse(User.objects.filter(email="new.starter@example.test").exists())

    def test_admin_approves_with_role(self):
        self.register()
        pending = User.objects.get(email="new.starter@example.test")

        self.client.force_login(make_user("admin"))
        listing = self.client.get(reverse("user_management"))
        self.assertIn(pending, listing.context["pending_users"])

        self.client.post(reverse("user_approve", args=[pending.pk]), {"role": "en"})

        pending = User.objects.get(pk=pending.pk)
        self.assertTrue(pending.is_active)
        self.assertEqual(pending.role, "en")
        self.assertTrue(pending.has_perm("medications.view_medication"))

    def test_only_admin_can_approve(self):
        self.register()
        pending = User.objects.get(email="new.starter@example.test")

        self.client.force_login(make_user("manager"))
        self.client.post(reverse("user_approve", args=[pending.pk]))

        self.assertFalse(User.objects.get(pk=pending.pk).is_active)


class PasswordResetTests(TestCase):

    def test_reset_email_link_sets_new_password(self):
        from django.core import mail

        make_user("rn", email="nurse@example.test")

        self.client.post(reverse("password_reset"), {"email": "nurse@example.test"})

        self.assertEqual(len(mail.outbox), 1)
        link = re.search(r"https?://[^/]+(/accounts/reset/\S+)", mail.outbox[0].body).group(1)

        response = self.client.get(link, follow=True)
        set_password_url = response.redirect_chain[-1][0]

        self.client.post(set_password_url, {
            "new_password1": "Brand-new-passphrase-77",
            "new_password2": "Brand-new-passphrase-77",
        })

        self.assertIsNotNone(authenticate(username="nurse@example.test", password="Brand-new-passphrase-77"))

    def test_unknown_email_sends_nothing_but_looks_the_same(self):
        from django.core import mail

        response = self.client.post(reverse("password_reset"), {"email": "nobody@example.test"})

        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)


class FacilityScopingTests(TestCase):
    """Staff only see residents of the facility they work in."""

    def setUp(self):
        from carecore.testing import make_facility, make_staff

        self.facility_a, self.ward_a, self.room_a = make_facility()
        self.facility_b, self.ward_b, self.room_b = make_facility()

        self.resident_a = make_resident(first_name="Alice", room=self.room_a)
        self.resident_b = make_resident(first_name="Bella", room=self.room_b)
        self.unassigned = make_resident(first_name="Una")

        self.nurse_a = make_user("rn")
        make_staff(self.nurse_a, self.facility_a, self.ward_a)

    def test_list_only_shows_own_facility_and_unassigned(self):
        self.client.force_login(self.nurse_a)

        names = {r.first_name for r in self.client.get(reverse("resident_list")).context["residents"]}

        self.assertEqual(names, {"Alice", "Una"})

    def test_other_facility_resident_is_404(self):
        self.client.force_login(self.nurse_a)

        self.assertEqual(self.client.get(reverse("resident_detail", args=[self.resident_b.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("resident_mar", args=[self.resident_b.pk])).status_code, 404)

    def test_dropdowns_exclude_other_facility_and_tampering_fails(self):
        from care.models import CareTask

        self.client.force_login(self.nurse_a)

        form = self.client.get(reverse("task_create")).context["form"]
        self.assertNotIn(self.resident_b, form.fields["resident"].queryset)

        self.client.post(reverse("task_create"), {
            "resident": self.resident_b.pk,
            "title": "Sneaky",
            "task_type": "other",
            "priority": "normal",
            "due_date": timezone.localdate().isoformat(),
            "status": "pending",
        })

        self.assertFalse(CareTask.objects.filter(title="Sneaky").exists())

    def test_facility_manager_sees_managed_facility(self):
        manager = make_user("manager")
        self.facility_b.manager = manager
        self.facility_b.save()

        self.client.force_login(manager)
        names = {r.first_name for r in self.client.get(reverse("resident_list")).context["residents"]}

        self.assertEqual(names, {"Bella", "Una"})

    def test_admin_sees_everyone(self):
        self.client.force_login(make_user("admin"))
        response = self.client.get(reverse("resident_list"))
        self.assertEqual(response.context["page"].paginator.count, 3)

    def test_alerts_are_scoped(self):
        from care.models import CareTask
        from insights.alerts import alerts_for

        for resident in (self.resident_a, self.resident_b):
            CareTask.objects.create(
                resident=resident,
                title=f"Overdue for {resident.first_name}",
                due_date=timezone.localdate() - timezone.timedelta(days=1),
            )

        titles = " ".join(alert.title for alert in alerts_for(self.nurse_a))

        self.assertIn("Alice", titles)
        self.assertNotIn("Bella", titles)


class PaginationTests(TestCase):

    def test_resident_list_paginates_and_keeps_filters(self):
        for index in range(30):
            make_resident(first_name=f"Res{index:02d}", care_level="high")

        self.client.force_login(make_user("admin"))
        response = self.client.get(reverse("resident_list") + "?care_level=high&page=2")

        self.assertEqual(len(response.context["residents"].object_list), 5)
        self.assertEqual(response.context["filter_query"], "care_level=high")
        self.assertContains(response, "Page 2 of 2")
