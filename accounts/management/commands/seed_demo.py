from datetime import date, time, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from facility.models import Facility, Ward, Room
from residents.models import Resident, ResidentContact
from staff.models import StaffMember, ResidentStaffAssignment
from care.models import (
    CarePlan,
    Assessment,
    CognitiveBehaviouralSupport,
    CareTask,
)
from medications.models import (
    Medication,
    MedicationAdministration,
)
from incidents.models import Incident
from appointments.models import Appointment


User = get_user_model()


class Command(BaseCommand):

    help = "Create realistic CareCore demo data."

    def handle(self, *args, **options):

        self.stdout.write(
            self.style.WARNING(
                "Creating CareCore demo data..."
            )
        )

        today = date.today()
        now = timezone.now()

        # ==================================================
        # USERS
        # ==================================================

        admin, _ = User.objects.get_or_create(
            email="admin@carecore.demo",
                defaults={
                    "username": "carecore_admin",
                    "first_name": "System",
                    "last_name": "Administrator",
                    "role": "admin",
                    "is_staff": True,
                    "is_superuser": True,
                },
            )

        admin.role = "admin"
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("CareCoreDemo123!")
        admin.save()

        manager, _ = User.objects.get_or_create(
    email="manager@carecore.demo",
    defaults={
        "username": "carecore_manager",
        "first_name": "Sarah",
        "last_name": "Manager",
        "role": "manager",
        "is_staff": True,
    },
)

        manager.role = "manager"
        manager.is_staff = True
        manager.set_password("CareCoreDemo123!")
        manager.save()

        rn_user, _ = User.objects.get_or_create(
    email="rn@carecore.demo",
    defaults={
        "username": "carecore_rn",
        "first_name": "James",
        "last_name": "Nurse",
        "role": "rn",
        "is_staff": True,
    },
)

        rn_user.role = "rn"
        rn_user.is_staff = True
        rn_user.set_password("CareCoreDemo123!")
        rn_user.save()

        care_user, _ = User.objects.get_or_create(
    email="careworker@carecore.demo",
    defaults={
        "username": "carecore_careworker",
        "first_name": "Emma",
        "last_name": "Careworker",
        "role": "care_worker",
        "is_staff": True,
    },
)

        care_user.role = "care_worker"
        care_user.is_staff = True
        care_user.set_password("CareCoreDemo123!")
        care_user.save()

        # ==================================================
        # FACILITY
        # ==================================================

        facility, _ = Facility.objects.get_or_create(
            name="CareCore Residential Facility",
            defaults={
                "address": "Demo Street 10",
                "phone": "+49 000 000000",
                "email": "facility@carecore.demo",
                "manager": manager,
                "number_of_rooms": 20,
                "occupancy": 2,
                "status": "active",
            },
        )

        ward, _ = Ward.objects.get_or_create(
            facility=facility,
            name="Maple Ward",
            defaults={
                "description": "General residential care ward.",
            },
        )

        room101, _ = Room.objects.get_or_create(
            ward=ward,
            room_number="101",
            defaults={
                "capacity": 1,
                "occupied": 1,
            },
        )

        room102, _ = Room.objects.get_or_create(
            ward=ward,
            room_number="102",
            defaults={
                "capacity": 1,
                "occupied": 1,
            },
        )

        # ==================================================
        # STAFF
        # ==================================================

        rn_staff, _ = StaffMember.objects.get_or_create(
            user=rn_user,
            defaults={
                "employee_id": "RN001",
                "phone": "+49 170 0000001",
                "facility": facility,
                "ward": ward,
                "employment_status": "active",
                "qualifications": "Registered Nurse",
            },
        )

        care_staff, _ = StaffMember.objects.get_or_create(
            user=care_user,
            defaults={
                "employee_id": "CW001",
                "phone": "+49 170 0000002",
                "facility": facility,
                "ward": ward,
                "employment_status": "active",
                "qualifications": "Personal Care Worker",
            },
        )

        # ==================================================
        # RESIDENTS
        # ==================================================

        resident1, _ = Resident.objects.get_or_create(
            first_name="Margaret",
            last_name="Wilson",
            defaults={
                "date_of_birth": date(1942, 4, 18),
                "gender": "female",
                "room": room101,
                "admission_date": date(2025, 6, 10),
                "status": "active",
                "care_level": "high",
                "mobility_needs": (
                    "Requires walking frame and supervision."
                ),
                "nutrition_needs": (
                    "Soft diet. Encourage fluids."
                ),
                "communication_needs": (
                    "Speak clearly and allow additional response time."
                ),
                "cognitive_support_needs": (
                    "Requires orientation prompts."
                ),
                "behavioural_support_needs": (
                    "Reassurance during periods of confusion."
                ),
            },
        )

        resident2, _ = Resident.objects.get_or_create(
            first_name="Robert",
            last_name="Taylor",
            defaults={
                "date_of_birth": date(1938, 9, 2),
                "gender": "male",
                "room": room102,
                "admission_date": date(2024, 11, 3),
                "status": "active",
                "care_level": "standard",
                "mobility_needs": (
                    "Independent with occasional supervision."
                ),
                "nutrition_needs": "Regular diet.",
                "communication_needs": (
                    "No specific communication support required."
                ),
            },
        )

        # ==================================================
        # CONTACTS
        # ==================================================

        ResidentContact.objects.get_or_create(
            resident=resident1,
            contact_type="family",
            name="Daniel Wilson",
            defaults={
                "relationship": "Son",
                "phone": "+49 170 0000003",
                "email": "daniel@example.com",
                "address": "Demo Address 1",
            },
        )

        ResidentContact.objects.get_or_create(
            resident=resident2,
            contact_type="emergency",
            name="Helen Taylor",
            defaults={
                "relationship": "Daughter",
                "phone": "+49 170 0000004",
                "email": "helen@example.com",
                "address": "Demo Address 2",
            },
        )

        # ==================================================
        # STAFF ASSIGNMENTS
        # ==================================================

        ResidentStaffAssignment.objects.get_or_create(
            staff=rn_staff,
            resident=resident1,
            role="nurse",
            start_date=today - timedelta(days=30),
            defaults={
                "is_active": True,
                "notes": "Primary nursing responsibility.",
            },
        )

        ResidentStaffAssignment.objects.get_or_create(
            staff=care_staff,
            resident=resident1,
            role="primary",
            start_date=today - timedelta(days=30),
            defaults={
                "is_active": True,
                "notes": "Primary care worker.",
            },
        )

        ResidentStaffAssignment.objects.get_or_create(
            staff=care_staff,
            resident=resident2,
            role="primary",
            start_date=today - timedelta(days=20),
            defaults={
                "is_active": True,
            },
        )

        # ==================================================
        # CARE PLAN
        # ==================================================

        CarePlan.objects.get_or_create(
            resident=resident1,
            status="active",
            defaults={
                "created_by": rn_user,
                "responsible_staff": rn_staff,
                "last_reviewed": today,
                "next_review": today + timedelta(days=30),
                "mobility": (
                    "Walking frame. Supervision required."
                ),
                "nutrition": (
                    "Soft diet and hydration monitoring."
                ),
                "personal_care": (
                    "Assistance with morning personal care."
                ),
                "communication": (
                    "Use clear, short instructions."
                ),
                "cognitive_support": (
                    "Provide orientation prompts."
                ),
                "behavioural_support": (
                    "Use calm reassurance."
                ),
                "notes": "Current care plan reviewed.",
            },
        )

        # ==================================================
        # ASSESSMENT
        # ==================================================

        Assessment.objects.get_or_create(
            resident=resident1,
            assessment_type="falls",
            assessment_date=today,
            defaults={
                "performed_by": rn_staff,
                "result": "High falls risk.",
                "notes": "Continue mobility supervision.",
                "next_review": today + timedelta(days=30),
            },
        )

        # ==================================================
        # COGNITIVE / BEHAVIOURAL SUPPORT
        # ==================================================

        CognitiveBehaviouralSupport.objects.get_or_create(
            resident=resident1,
            defaults={
                "support_requirements": (
                    "Regular reassurance and orientation."
                ),
                "known_triggers": (
                    "Unfamiliar environments."
                ),
                "communication_preferences": (
                    "Simple and clear instructions."
                ),
                "behaviour_observations": (
                    "Occasional confusion in evenings."
                ),
                "de_escalation_strategies": (
                    "Calm voice and reassurance."
                ),
                "care_instructions": (
                    "Maintain predictable routine."
                ),
            },
        )

        # ==================================================
        # CARE TASKS
        # ==================================================

        CareTask.objects.get_or_create(
            resident=resident1,
            title="Morning personal care",
            due_date=today,
            defaults={
                "assigned_to": care_staff,
                "description": (
                    "Assist with morning hygiene and dressing."
                ),
                "task_type": "personal_care",
                "priority": "normal",
                "due_time": time(8, 0),
            },
        )

        CareTask.objects.get_or_create(
            resident=resident1,
            title="Mobility check",
            due_date=today - timedelta(days=1),
            defaults={
                "assigned_to": care_staff,
                "description": (
                    "Check mobility and walking frame use."
                ),
                "task_type": "mobility",
                "priority": "high",
            },
        )

        # ==================================================
        # MEDICATION
        # ==================================================

        medication, _ = Medication.objects.get_or_create(
            resident=resident1,
            name="Paracetamol",
            defaults={
                "dose": "500 mg",
                "route": "Oral",
                "frequency": "Twice daily",
                "start_date": today - timedelta(days=10),
                "prescriber": "Dr. Demo",
                "status": "active",
            },
        )

        MedicationAdministration.objects.create(
            medication=medication,
            administered_by=rn_staff,
            administered_at=now - timedelta(hours=2),
            status="administered",
            notes="Administered as prescribed.",
        )

        # ==================================================
        # INCIDENT
        # ==================================================

        Incident.objects.get_or_create(
            resident=resident1,
            category="fall",
            incident_date=now - timedelta(days=1),
            defaults={
                "reported_by": care_staff,
                "severity": "medium",
                "description": (
                    "Resident experienced a fall near the bedroom."
                ),
                "immediate_action": (
                    "Resident assessed and assisted safely."
                ),
                "status": "resolved",
                "investigation_notes": (
                    "No serious injury identified."
                ),
                "corrective_action": (
                    "Continue falls-risk precautions."
                ),
                "resolved_at": now - timedelta(hours=20),
            },
        )

        # ==================================================
        # APPOINTMENT
        # ==================================================

        Appointment.objects.get_or_create(
            resident=resident1,
            title="GP Review",
            appointment_date=today + timedelta(days=2),
            defaults={
                "assigned_staff": rn_staff,
                "appointment_type": "medical",
                "start_time": time(10, 0),
                "end_time": time(11, 0),
                "location": "Local Medical Centre",
                "provider": "Dr. Demo",
                "status": "scheduled",
                "notes": "Routine clinical review.",
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                "CareCore demo data created successfully."
            )
        )