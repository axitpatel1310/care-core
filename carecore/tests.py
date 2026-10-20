import re
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import URLPattern, URLResolver, get_resolver, reverse

from accounts.models import User


def iter_patterns(resolver, prefix=""):

    for pattern in resolver.url_patterns:

        if isinstance(pattern, URLResolver):
            if str(pattern.pattern).startswith("admin"):
                continue
            yield from iter_patterns(pattern, prefix + str(pattern.pattern))

        elif isinstance(pattern, URLPattern):
            yield prefix + str(pattern.pattern), pattern.name


PUBLIC_PAGES = {
    "login",
    "register",
    "password_reset",
    "password_reset_done",
    "password_reset_complete",
}


class PageSmokeTests(TestCase):
    """Render every GET page as every role against the demo data set: no page may error."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())

    def urls(self):

        for pattern, name in iter_patterns(get_resolver()):

            if "logout" in pattern or "media" in pattern or "(?P" in pattern or "<uidb64>" in pattern:
                continue

            url = "/" + re.sub(r"<int:\w+>", "1", pattern)
            url = re.sub(r"<slug:\w+>", "incidents", url)

            yield url, name

    def test_every_page_renders_for_every_role(self):

        for email in (
            "admin@carecore.demo",
            "manager@carecore.demo",
            "rn@carecore.demo",
            "careworker@carecore.demo",
        ):
            self.client.force_login(User.objects.get(email=email))

            for url, name in self.urls():
                with self.subTest(user=email, url=url):
                    response = self.client.get(url)
                    if name == "document_download":
                        continue  # demo documents have no file; covered in compliance tests

                    # 405: POST-only actions such as approving an account.
                    self.assertIn(
                        response.status_code,
                        (200, 302, 403, 405),
                        f"{name} returned {response.status_code}",
                    )

    def test_anonymous_users_are_redirected_to_login(self):

        for url, name in self.urls():

            if name in PUBLIC_PAGES:
                continue

            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, (302, 405))
                if response.status_code == 302:
                    self.assertIn("/accounts/login/", response["Location"])

    def test_seed_demo_is_idempotent(self):

        counts = User.objects.count()
        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(User.objects.count(), counts)


class FormSubmissionTests(TestCase):
    """Create/update flows in the original modules save data and redirect."""

    @classmethod
    def setUpTestData(cls):
        from datetime import date

        from carecore.testing import make_facility, make_resident, make_staff, make_user

        cls.admin = make_user("admin")
        cls.facility, cls.ward, cls.room = make_facility()
        cls.room.capacity = 5
        cls.room.save()
        cls.staff_user = make_user("rn")
        cls.staff = make_staff(cls.staff_user, cls.facility, cls.ward)
        cls.resident = make_resident(room=cls.room)
        cls.today = date.today().isoformat()

    def setUp(self):
        self.client.force_login(self.admin)

    def post_creates(self, url_name, data, model, args=None, **lookup):
        response = self.client.post(reverse(url_name, args=args or []), data)
        self.assertEqual(response.status_code, 302, getattr(response, "context", {}) and response.context.get("form") and response.context["form"].errors)
        self.assertTrue(model.objects.filter(**lookup).exists(), f"{url_name} did not save")
        return response

    def test_resident_and_contact(self):
        from residents.models import Resident, ResidentContact

        self.post_creates("resident_create", {
            "first_name": "Grace", "last_name": "Hopper", "date_of_birth": "1936-12-09",
            "gender": "female", "room": self.room.pk, "admission_date": self.today,
            "status": "active", "care_level": "high",
        }, Resident, first_name="Grace")

        self.post_creates("contact_create", {
            "contact_type": "family", "name": "Vincent Hopper", "relationship": "Son", "phone": "0123",
        }, ResidentContact, args=[self.resident.pk], name="Vincent Hopper")

    def test_care_records(self):
        from care.models import Assessment, CarePlan, CareTask

        self.post_creates("care_plan_create", {
            "resident": self.resident.pk, "responsible_staff": self.staff.pk, "status": "active",
            "next_review": self.today,
        }, CarePlan, resident=self.resident)

        self.post_creates("assessment_create", {
            "resident": self.resident.pk, "assessment_type": "falls", "assessment_date": self.today,
            "performed_by": self.staff.pk, "result": "High risk",
        }, Assessment, result="High risk")

        self.post_creates("task_create", {
            "resident": self.resident.pk, "assigned_to": self.staff.pk, "title": "Reposition",
            "task_type": "personal_care", "priority": "high", "due_date": self.today, "status": "pending",
        }, CareTask, title="Reposition")

        task = CareTask.objects.get(title="Reposition")
        self.client.post(reverse("task_start", args=[task.pk]))
        task.refresh_from_db()
        self.assertEqual(task.status, "in_progress")

        self.client.post(reverse("task_complete", args=[task.pk]), {"notes": "Done"})
        task.refresh_from_db()
        self.assertEqual(task.status, "completed")
        self.assertIsNotNone(task.completed_at)

    def test_incident_lifecycle(self):
        from incidents.models import Incident

        self.post_creates("incident_create", {
            "resident": self.resident.pk, "incident_date": f"{self.today}T09:00", "category": "fall",
            "severity": "medium", "description": "Slipped", "status": "open",
        }, Incident, description="Slipped")

        incident = Incident.objects.get(description="Slipped")

        self.client.post(reverse("incident_investigate", args=[incident.pk]), {
            "status": "investigating", "investigation_notes": "Wet floor", "corrective_action": "Signage",
        })
        incident.refresh_from_db()
        self.assertEqual(incident.investigation_notes, "Wet floor")

        self.client.post(reverse("incident_resolve", args=[incident.pk]))
        incident.refresh_from_db()
        self.assertEqual(incident.status, "resolved")
        self.assertIsNotNone(incident.resolved_at)

    def test_appointment_crud(self):
        from appointments.models import Appointment

        self.post_creates("appointment_create", {
            "resident": self.resident.pk, "title": "Dentist", "appointment_type": "dental",
            "appointment_date": self.today, "start_time": "10:00", "status": "scheduled",
        }, Appointment, title="Dentist")

        appointment = Appointment.objects.get(title="Dentist")
        self.client.post(reverse("appointment_edit", args=[appointment.pk]), {
            "resident": self.resident.pk, "title": "Dentist", "appointment_type": "dental",
            "appointment_date": self.today, "start_time": "11:00", "status": "confirmed",
        })
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, "confirmed")

        self.client.post(reverse("appointment_delete", args=[appointment.pk]))
        self.assertFalse(Appointment.objects.filter(pk=appointment.pk).exists())

    def test_staff_and_assignment(self):
        from carecore.testing import make_user
        from staff.models import ResidentStaffAssignment, StaffMember

        new_user = make_user("care_worker")

        self.post_creates("staff_create", {
            "user": new_user.pk, "employee_id": "CW999", "facility": self.facility.pk,
            "ward": self.ward.pk, "employment_status": "active",
        }, StaffMember, employee_id="CW999")

        self.post_creates("assignment_create", {
            "staff": self.staff.pk, "resident": self.resident.pk, "role": "nurse",
            "start_date": self.today, "is_active": "on",
        }, ResidentStaffAssignment, staff=self.staff, role="nurse")

    def test_facility_structure(self):
        from facility.models import Facility, Room, Ward

        self.post_creates("facility_create", {
            "name": "Second Home", "address": "2 Road", "status": "active",
        }, Facility, name="Second Home")

        facility = Facility.objects.get(name="Second Home")

        self.post_creates("ward_create", {"facility": facility.pk, "name": "Birch"}, Ward, name="Birch")
        ward = Ward.objects.get(name="Birch")

        self.post_creates("room_create", {"ward": ward.pk, "room_number": "B1", "capacity": 2}, Room, room_number="B1")

        facility.refresh_from_db()
        self.assertEqual(facility.number_of_rooms, 1)
