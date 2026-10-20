import random
from datetime import date, datetime, time, timedelta

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
    MedicationDoseTime,
)
from incidents.models import Incident
from appointments.models import Appointment
from observations.models import Observation
from observations.services import escalate_if_required
from compliance.models import (
    Audit,
    AuditControl,
    ComplianceDocument,
    CorrectiveAction,
    Risk,
)


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

        en_user, _ = User.objects.get_or_create(
            email="en@carecore.demo",
            defaults={
                "username": "carecore_en",
                "first_name": "Priya",
                "last_name": "Enrolled",
                "role": "en",
            },
        )

        en_user.role = "en"
        en_user.set_password("CareCoreDemo123!")
        en_user.save()

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
            },
        )

        room102, _ = Room.objects.get_or_create(
            ward=ward,
            room_number="102",
            defaults={
                "capacity": 1,
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

        StaffMember.objects.get_or_create(
            user=en_user,
            defaults={
                "employee_id": "EN001",
                "facility": facility,
                "ward": ward,
                "employment_status": "active",
                "qualifications": "Diploma of Nursing (Enrolled Nurse)",
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

        for dose_time in (time(8, 0), time(20, 0)):
            MedicationDoseTime.objects.get_or_create(
                medication=medication,
                time=dose_time,
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

        # ==================================================
        # CLINICAL HISTORY & GOVERNANCE
        # ==================================================

        room103, _ = Room.objects.get_or_create(
            ward=room101.ward,
            room_number="103",
            defaults={"capacity": 1},
        )

        resident3, _ = Resident.objects.get_or_create(
            first_name="Dorothy",
            last_name="Evans",
            defaults={
                "date_of_birth": date(1935, 1, 27),
                "gender": "female",
                "room": room103,
                "admission_date": today - timedelta(days=400),
                "status": "active",
                "care_level": "complex",
                "mobility_needs": "Hoist transfers, two staff.",
                "nutrition_needs": "Thickened fluids (level 2).",
                "communication_needs": "Hearing aids, left ear.",
                "cognitive_support_needs": "Moderate dementia.",
            },
        )

        ResidentStaffAssignment.objects.get_or_create(
            staff=rn_staff,
            resident=resident3,
            role="nurse",
            defaults={"start_date": today - timedelta(days=90)},
        )

        if not Observation.objects.exists():
            self.seed_observations(
                [resident1, resident2, resident3],
                rn_staff,
                now,
            )

        if Incident.objects.count() < 5:
            self.seed_incident_history(
                [resident1, resident2, resident3],
                care_staff,
                now,
            )

        if MedicationAdministration.objects.count() < 10:
            self.seed_medication_history(
                [resident1, resident2, resident3],
                [rn_staff, care_staff],
                today,
                now,
            )

        if not Risk.objects.exists():
            self.seed_compliance(
                manager,
                rn_staff,
                today,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "CareCore demo data created successfully."
            )
        )

    def seed_observations(self, residents, staff, now):

        rng = random.Random(42)
        stable, improving, deteriorating = residents

        # (resident, hours ago, rr, spo2, sbp, pulse, temp, consciousness, on_oxygen)
        profiles = []

        for hours_ago in range(96, -1, -12):
            profiles.append((stable, hours_ago, 16, 97, 128, 74, "36.8", "A", False))

        for step, hours_ago in enumerate(range(72, -1, -8)):
            profiles.append((
                improving, hours_ago, 22 - step, 93 + min(step, 4),
                104 + step * 3, 102 - step * 3, "38.2" if step < 3 else "37.1", "A", False,
            ))

        for step, hours_ago in enumerate(range(48, 0, -6)):
            profiles.append((
                deteriorating, hours_ago, 18 + step, 96 - step,
                122 - step * 4, 84 + step * 5, str(37.0 + step * 0.25),
                "A" if step < 6 else "C", step >= 5,
            ))

        for resident, hours_ago, rr, spo2, sbp, pulse, temp, acvpu, oxygen in profiles:

            observation = Observation.objects.create(
                resident=resident,
                recorded_by=staff,
                recorded_at=now - timedelta(hours=hours_ago, minutes=rng.randint(0, 40)),
                respiratory_rate=rr,
                spo2=min(spo2, 100),
                on_oxygen=oxygen,
                systolic_bp=sbp,
                diastolic_bp=sbp - rng.randint(40, 55),
                pulse=pulse,
                consciousness=acvpu,
                temperature=temp,
            )

            if hours_ago <= 6:
                escalate_if_required(observation)

    def seed_incident_history(self, residents, staff, now):

        rng = random.Random(7)

        categories = ["fall", "fall", "medication_error", "behavioural", "injury", "environmental"]
        severities = ["low", "low", "medium", "medium", "high", "critical"]

        for _ in range(28):

            occurred = now - timedelta(days=rng.randint(2, 330), hours=rng.randint(0, 23))
            resolved = rng.random() < 0.85

            Incident.objects.create(
                resident=rng.choice(residents),
                reported_by=staff,
                incident_date=occurred,
                category=rng.choice(categories),
                severity=rng.choice(severities),
                description="Demo incident generated for analytics.",
                immediate_action="Resident checked and made safe.",
                status="resolved" if resolved else "investigating",
                resolved_at=occurred + timedelta(hours=rng.randint(2, 96)) if resolved else None,
            )

        Incident.objects.create(
            resident=residents[2],
            reported_by=staff,
            incident_date=now - timedelta(hours=5),
            category="fall",
            severity="high",
            description="Found on floor beside bed during night check.",
            immediate_action="Post-fall observations commenced; GP informed.",
            status="open",
        )

    def seed_medication_history(self, residents, staff, today, now):

        rng = random.Random(11)

        catalogue = [
            ("Amlodipine", "5 mg", "Oral", "Once daily", ["08:00"]),
            ("Metformin", "500 mg", "Oral", "Twice daily", ["08:00", "18:00"]),
            ("Donepezil", "10 mg", "Oral", "Once daily at night", ["21:00"]),
        ]

        for resident, (name, dose, route, frequency, times) in zip(residents, catalogue):

            medication, _ = Medication.objects.get_or_create(
                resident=resident,
                name=name,
                defaults={
                    "dose": dose,
                    "route": route,
                    "frequency": frequency,
                    "start_date": today - timedelta(days=120),
                    "prescriber": "Dr. Demo",
                    "status": "active",
                },
            )

            for value in times:
                MedicationDoseTime.objects.get_or_create(
                    medication=medication,
                    time=time(*map(int, value.split(":"))),
                )

            # 12 weeks of recorded scheduled doses, up to (not including) today.
            for day in range(84, 0, -1):

                for value in times:

                    scheduled = timezone.make_aware(
                        datetime.combine(today - timedelta(days=day), time(*map(int, value.split(":"))))
                    )

                    roll = rng.random()
                    status = (
                        "administered" if roll < 0.9
                        else "refused" if roll < 0.95
                        else "missed" if roll < 0.98
                        else "withheld"
                    )

                    MedicationAdministration.objects.create(
                        medication=medication,
                        administered_by=rng.choice(staff),
                        administered_at=scheduled + timedelta(minutes=rng.randint(-20, 45)),
                        scheduled_for=scheduled,
                        status=status,
                        notes="" if status == "administered" else "Reason recorded on the paper MAR.",
                    )

        Medication.objects.get_or_create(
            resident=residents[0],
            name="Paracetamol PRN",
            defaults={
                "dose": "1 g",
                "route": "Oral",
                "frequency": "Up to four times daily as required for pain",
                "as_required": True,
                "start_date": today - timedelta(days=30),
                "prescriber": "Dr. Demo",
                "status": "active",
            },
        )

    def seed_compliance(self, manager, owner, today):

        for title, doc_type, version, next_review in [
            ("Medication Management Policy", "policy", "3.1", today + timedelta(days=120)),
            ("Falls Prevention Procedure", "procedure", "2.0", today - timedelta(days=12)),
            ("Infection Control Guideline", "guideline", "1.4", today + timedelta(days=45)),
            ("Recognising Deterioration (NEWS2) Procedure", "procedure", "1.0", today + timedelta(days=300)),
        ]:
            ComplianceDocument.objects.create(
                title=title,
                document_type=doc_type,
                version=version,
                owner=manager,
                last_reviewed=next_review - timedelta(days=365),
                next_review=next_review,
            )

        for description, category, likelihood, impact, review in [
            ("Residents at high risk of falls at night", "clinical", 4, 4, today + timedelta(days=30)),
            ("Agency staff unfamiliar with residents", "staff", 3, 3, today - timedelta(days=5)),
            ("Medication omissions during handover", "medication", 3, 4, today + timedelta(days=14)),
            ("Wet floors in communal bathroom", "environment", 2, 3, today + timedelta(days=60)),
            ("Mandatory training compliance below target", "compliance", 4, 2, today + timedelta(days=21)),
        ]:
            Risk.objects.create(
                description=description,
                category=category,
                likelihood=likelihood,
                impact=impact,
                owner=owner,
                review_date=review,
                mitigation="Controls documented in the related procedure.",
            )

        audit = Audit.objects.create(
            title="Quarterly Medication Audit",
            description="Review of MAR completeness, storage and PRN documentation.",
            created_by=manager,
            start_date=today - timedelta(days=20),
            completion_date=today - timedelta(days=14),
            status="completed",
        )

        controls = [
            ("All administrations signed on the MAR", "passed", ""),
            ("Controlled drugs register reconciled daily", "partial", "Two days without a second signature."),
            ("Fridge temperatures logged twice daily", "failed", "Logs missing for 6 of 14 days."),
            ("PRN effectiveness documented", "passed", ""),
        ]

        for requirement, result, finding in controls:
            control = AuditControl.objects.create(
                audit=audit,
                requirement=requirement,
                result=result,
                finding=finding,
                evidence="Sampled 20 MAR charts.",
            )

            if result == "failed":
                CorrectiveAction.objects.create(
                    title="Reinstate twice-daily fridge temperature checks",
                    description=finding,
                    owner=owner,
                    priority="high",
                    due_date=today - timedelta(days=2),
                    source_finding=control,
                )

        CorrectiveAction.objects.create(
            title="Install sensor mats for high falls-risk residents",
            owner=owner,
            priority="medium",
            due_date=today + timedelta(days=21),
            status="in_progress",
            source_incident=Incident.objects.filter(category="fall").order_by("-incident_date").first(),
        )