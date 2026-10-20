"""Shared factories for the CareCore test suite."""

from datetime import date, timedelta

from django.utils import timezone

from accounts.models import User
from facility.models import Facility, Room, Ward
from residents.models import Resident
from staff.models import StaffMember


def make_user(role="care_worker", email=None, **extra):

    email = email or f"{role}-{User.objects.count()}@example.test"

    return User.objects.create_user(
        username=email,
        email=email,
        password="Test-password-123",
        role=role,
        first_name=extra.pop("first_name", role.title()),
        last_name=extra.pop("last_name", "User"),
        **extra,
    )


def make_facility():

    facility = Facility.objects.create(name="Test Facility", address="1 Test Street")
    ward = Ward.objects.create(facility=facility, name="Oak Ward")
    room = Room.objects.create(ward=ward, room_number="1")

    return facility, ward, room


def make_staff(user, facility=None, ward=None):

    if facility is None:
        facility, ward, _ = make_facility()

    return StaffMember.objects.create(
        user=user,
        employee_id=f"EMP{user.pk:04d}",
        facility=facility,
        ward=ward,
    )


def make_resident(**extra):

    defaults = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "date_of_birth": date(1940, 1, 1),
        "gender": "female",
        "admission_date": timezone.localdate() - timedelta(days=100),
        "status": "active",
        "care_level": "standard",
    }
    defaults.update(extra)

    return Resident.objects.create(**defaults)


NORMAL_VITALS = {
    "respiratory_rate": 16,
    "spo2": 97,
    "on_oxygen": False,
    "systolic_bp": 125,
    "pulse": 72,
    "consciousness": "A",
    "temperature": "36.8",
}
