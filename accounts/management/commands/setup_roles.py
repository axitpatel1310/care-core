from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


ROLE_PERMISSIONS = {

    "Administrator": {
        "*": ["view", "add", "change", "delete"],
    },

    "Manager": {
        "residents.resident": ["view", "add", "change", "delete"],
        "residents.residentcontact": ["view", "add", "change", "delete"],

        "staff.staffmember": ["view", "add", "change", "delete"],
        "staff.residentstaffassignment": ["view", "add", "change", "delete"],

        "care.careplan": ["view", "add", "change", "delete"],
        "care.assessment": ["view", "add", "change", "delete"],
        "care.caretask": ["view", "add", "change", "delete"],
        "care.cognitivebehaviouralsupport": ["view", "add", "change", "delete"],

        "medications.medication": ["view", "add", "change"],
        "medications.medicationadministration": ["view", "add", "change"],

        "incidents.incident": ["view", "add", "change", "delete"],

        "appointments.appointment": ["view", "add", "change", "delete"],

        "facility.facility": ["view"],
        "facility.ward": ["view"],
        "facility.room": ["view"],
    },

    "RN": {
        "residents.resident": ["view", "add", "change"],
        "residents.residentcontact": ["view", "add", "change"],
        "care.careplan": ["view", "add", "change"],
        "care.assessment": ["view", "add", "change"],
        "care.caretask": ["view", "add", "change"],
        "care.cognitivebehaviouralsupport": ["view", "add", "change"],
        "medications.medication": ["view", "add", "change"],
        "medications.medicationadministration": ["view", "add", "change"],
        "incidents.incident": ["view", "add", "change"],
        "appointments.appointment": ["view", "add", "change"],
        "facility.room": ["view"],
        "facility.ward": ["view"],
    },

    "EN": {
        "residents.resident": ["view", "change"],
        "residents.residentcontact": ["view", "add", "change"],
        "care.careplan": ["view", "add", "change"],
        "care.assessment": ["view", "add", "change"],
        "care.caretask": ["view", "add", "change"],
        "care.cognitivebehaviouralsupport": ["view", "add", "change"],
        "medications.medication": ["view", "add"],
        "medications.medicationadministration": ["view", "add"],
        "incidents.incident": ["view", "add"],
        "appointments.appointment": ["view", "add", "change"],
        "facility.room": ["view"],
        "facility.ward": ["view"],
    },

    "Personal Care Worker": {
        "residents.resident": ["view"],
        "residents.residentcontact": ["view"],
        "care.careplan": ["view"],
        "care.assessment": ["view"],
        "care.caretask": ["view", "add", "change"],
        "care.cognitivebehaviouralsupport": ["view"],
        "medications.medication": ["view"],
        "medications.medicationadministration": ["view", "add"],
        "incidents.incident": ["view", "add"],
        "appointments.appointment": ["view"],
        "facility.room": ["view"],
        "facility.ward": ["view"],
    },
}


class Command(BaseCommand):

    help = "Create and configure CareCore role groups."

    def handle(self, *args, **options):

        for group_name, rules in ROLE_PERMISSIONS.items():

            group, created = Group.objects.get_or_create(
                name=group_name
            )

            group.permissions.clear()

            if "*" in rules:

                permissions = Permission.objects.all()

                for permission in permissions:

                    group.permissions.add(permission)

            else:

                for model_key, actions in rules.items():

                    app_label, model_name = model_key.split(".")

                    for action in actions:

                        codename = f"{action}_{model_name}"

                        try:

                            permission = Permission.objects.get(
                                content_type__app_label=app_label,
                                codename=codename,
                            )

                            group.permissions.add(permission)

                        except Permission.DoesNotExist:

                            self.stdout.write(
                                self.style.WARNING(
                                    f"Missing permission: "
                                    f"{app_label}.{codename}"
                                )
                            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Configured group: {group_name}"
                )
            )