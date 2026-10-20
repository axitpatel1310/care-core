from django.contrib.auth.models import Group, Permission


# Maps the User.role value to the permission group that carries its rights.
ROLE_GROUPS = {
    "admin": "Administrator",
    "manager": "Manager",
    "rn": "RN",
    "en": "EN",
    "care_worker": "Personal Care Worker",
}


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


def configure_role_groups(log=None):

    for group_name, rules in ROLE_PERMISSIONS.items():

        group, created = Group.objects.get_or_create(
            name=group_name
        )

        if "*" in rules:

            group.permissions.set(
                Permission.objects.all()
            )

        else:

            permissions = []

            for model_key, actions in rules.items():

                app_label, model_name = model_key.split(".")

                for action in actions:

                    codename = f"{action}_{model_name}"

                    permission = Permission.objects.filter(
                        content_type__app_label=app_label,
                        codename=codename,
                    ).first()

                    if permission:
                        permissions.append(permission)

                    elif log:
                        log(f"Missing permission: {app_label}.{codename}")

            group.permissions.set(permissions)

        if log:
            log(f"Configured group: {group_name}")


def sync_user_role_group(user):

    role_group_names = set(ROLE_GROUPS.values())

    target_name = ROLE_GROUPS.get(user.role)

    stale_groups = user.groups.filter(
        name__in=role_group_names,
    ).exclude(
        name=target_name,
    )

    if stale_groups.exists():
        user.groups.remove(*stale_groups)

    if target_name:

        group, _ = Group.objects.get_or_create(
            name=target_name
        )

        user.groups.add(group)
