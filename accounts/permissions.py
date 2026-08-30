
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


ROLE_PERMISSIONS = {

    "admin": {
        "*": ["view", "add", "change", "delete"],
    },

    "manager": {
        "residents.resident": ["view", "add", "change"],
        "residents.residentcontact": ["view", "add", "change", "delete"],

        "staff.staffmember": ["view", "add", "change"],
        "staff.residentstaffassignment": ["view", "add", "change", "delete"],

        "care.careplan": ["view", "add", "change"],
        "care.assessment": ["view", "add", "change"],
        "care.caretask": ["view", "add", "change", "delete"],
        "care.cognitivebehaviouralsupport": ["view", "add", "change"],

        "medications.medication": ["view", "add", "change"],
        "medications.medicationadministration": ["view", "add", "change"],

        "incidents.incident": ["view", "add", "change", "delete"],

        "appointments.appointment": ["view", "add", "change", "delete"],

        "facility.facility": ["view"],
        "facility.ward": ["view"],
        "facility.room": ["view"],
    },

    "rn": {
        "residents.resident": ["view", "add", "change"],
        "residents.residentcontact": ["view", "add", "change"],

        "staff.staffmember": ["view"],

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

    "en": {
        "residents.resident": ["view", "change"],
        "residents.residentcontact": ["view", "add", "change"],

        "staff.staffmember": ["view"],

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

    "care_worker": {
        "residents.resident": ["view"],
        "residents.residentcontact": ["view"],

        "staff.staffmember": ["view"],

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

def has_role_permission(user, module, action):

    if not user.is_authenticated:
        return False

    permissions = ROLE_PERMISSIONS.get(
        user.role,
        {},
    )

    if "*" in permissions:
        return action in permissions["*"]

    return action in permissions.get(
        module,
        [],
    )

def role_required(module, action):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not has_role_permission(
                request.user,
                module,
                action,
            ):

                messages.error(
                    request,
                    "You do not have permission to perform this action.",
                )

                return redirect("dashboard")

            return view_func(
                request,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator
