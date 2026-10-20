from django.test import TestCase
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
