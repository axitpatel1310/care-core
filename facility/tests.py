from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from carecore.testing import make_facility, make_resident, make_user
from residents.forms import ResidentForm

from .forms import RoomForm
from .models import Room


class DerivedOccupancyTests(TestCase):

    def setUp(self):
        self.facility, self.ward, self.room = make_facility()
        self.room.capacity = 2
        self.room.save()
        self.other_room = Room.objects.create(ward=self.ward, room_number="2", capacity=1)

    def occupancy(self):
        self.room.refresh_from_db()
        self.other_room.refresh_from_db()
        self.facility.refresh_from_db()
        return self.room.occupied, self.other_room.occupied, self.facility.occupancy

    def test_occupancy_follows_residents(self):
        resident = make_resident(room=self.room)
        self.assertEqual(self.occupancy(), (1, 0, 1))

        resident.room = self.other_room
        resident.save()
        self.assertEqual(self.occupancy(), (0, 1, 1))

        resident.status = "discharged"
        resident.save()
        self.assertEqual(self.occupancy(), (0, 0, 0))

        resident.status = "hospital"  # bed is held
        resident.save()
        self.assertEqual(self.occupancy(), (0, 1, 1))

        resident.delete()
        self.assertEqual(self.occupancy(), (0, 0, 0))

    def test_facility_room_count_is_derived(self):
        self.facility.refresh_from_db()
        self.assertEqual(self.facility.number_of_rooms, 2)

    def test_full_room_rejects_another_resident(self):
        make_resident(room=self.other_room)

        form = ResidentForm(data={
            "first_name": "Ann", "last_name": "Other", "date_of_birth": "1940-01-01",
            "gender": "female", "room": self.other_room.pk, "admission_date": "2025-01-01",
            "status": "active", "care_level": "standard",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("is full", str(form.errors["room"]))

    def test_discharged_resident_does_not_need_a_bed(self):
        make_resident(room=self.other_room)

        form = ResidentForm(data={
            "first_name": "Ann", "last_name": "Other", "date_of_birth": "1940-01-01",
            "gender": "female", "room": self.other_room.pk, "admission_date": "2025-01-01",
            "status": "discharged", "care_level": "standard",
        })

        self.assertTrue(form.is_valid(), form.errors)

    def test_capacity_cannot_drop_below_occupants(self):
        make_resident(room=self.room)
        make_resident(room=self.room)

        form = RoomForm(data={"ward": self.ward.pk, "room_number": "1", "capacity": 1}, instance=self.room)

        self.assertFalse(form.is_valid())

    def test_occupancy_fields_not_editable_in_forms(self):
        self.client.force_login(make_user("admin"))
        form = self.client.get(reverse("room_create")).context["form"]
        self.assertNotIn("occupied", form.fields)


class OverCapacityTests(TestCase):
    """Rooms that were already over-full before capacity checks existed are surfaced, not hidden."""

    def setUp(self):
        self.facility, self.ward, self.room = make_facility()
        make_resident(room=self.room)
        # Bypass form validation, as legacy data would have.
        make_resident(first_name="Extra", room=self.room)
        self.room.refresh_from_db()

    def test_alert_raised(self):
        from carecore.testing import make_staff
        from insights.alerts import alerts_for

        nurse = make_user("rn")
        make_staff(nurse, self.facility, self.ward)

        titles = [alert.title for alert in alerts_for(nurse)]

        self.assertIn(f"Room {self.room} over capacity", titles)

    def test_report_command_lists_room(self):
        from io import StringIO

        from django.core.management import call_command

        out = StringIO()
        call_command("occupancy_report", stdout=out)

        self.assertIn("2 of 1 beds", out.getvalue())
        self.assertIn("Extra", out.getvalue())

    def test_facility_page_shows_badge(self):
        self.client.force_login(make_user("admin"))
        response = self.client.get(reverse("facility_detail", args=[self.facility.pk]))
        self.assertContains(response, "Over capacity")


class FacilityBackfillMigrationTests(TransactionTestCase):
    """The facility backfill migrations assign existing residents and incidents correctly."""

    migrate_from = [("residents", "0001_initial"), ("incidents", "0001_initial")]
    migrate_to = [("residents", "0002_resident_facility"), ("incidents", "0002_incident_facility")]

    def test_backfill(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        from django.utils import timezone

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old = executor.loader.project_state(self.migrate_from).apps

        Facility = old.get_model("facility", "Facility")
        Ward = old.get_model("facility", "Ward")
        Room = old.get_model("facility", "Room")
        Resident = old.get_model("residents", "Resident")
        Incident = old.get_model("incidents", "Incident")

        facility = Facility.objects.create(name="Only Home", address="x")
        room = Room.objects.create(ward=Ward.objects.create(facility=facility, name="W"), room_number="1")

        common = {"date_of_birth": "1940-01-01", "gender": "female", "admission_date": "2025-01-01"}
        roomed = Resident.objects.create(first_name="In", last_name="Room", room=room, **common)
        roomless = Resident.objects.create(first_name="No", last_name="Room", **common)
        incident = Incident.objects.create(
            resident=roomed, incident_date=timezone.now(), category="fall", severity="low", description="x",
        )
        loose = Incident.objects.create(
            incident_date=timezone.now(), category="environmental", severity="low", description="y",
        )

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        new = executor.loader.project_state(self.migrate_to).apps

        Resident = new.get_model("residents", "Resident")
        Incident = new.get_model("incidents", "Incident")

        self.assertEqual(Resident.objects.get(pk=roomed.pk).facility_id, facility.pk)
        self.assertEqual(Resident.objects.get(pk=roomless.pk).facility_id, facility.pk)  # only facility
        self.assertEqual(Incident.objects.get(pk=incident.pk).facility_id, facility.pk)
        self.assertEqual(Incident.objects.get(pk=loose.pk).facility_id, facility.pk)

        # Leave the schema fully migrated for the rest of the suite.
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
