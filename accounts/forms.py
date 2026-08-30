from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


ROLE_PERMISSIONS = {

    "admin": {
        "all": True,
    },

    "manager": {
        "residents": ["view", "add", "change", "delete"],
        "staff": ["view", "add", "change", "delete"],
        "care": ["view", "add", "change", "delete"],
        "medications": ["view", "add", "change"],
        "incidents": ["view", "add", "change", "delete"],
        "appointments": ["view", "add", "change", "delete"],
    },

    "rn": {
        "residents": ["view", "add", "change"],
        "staff": ["view"],
        "care": ["view", "add", "change"],
        "medications": ["view", "add", "change"],
        "incidents": ["view", "add", "change"],
        "appointments": ["view", "add", "change"],
    },

    "en": {
        "residents": ["view", "change"],
        "staff": ["view"],
        "care": ["view", "add", "change"],
        "medications": ["view", "add"],
        "incidents": ["view", "add"],
        "appointments": ["view", "add", "change"],
    },

    "care_worker": {
        "residents": ["view"],
        "staff": ["view"],
        "care": ["view", "add", "change"],
        "medications": ["view", "add"],
        "incidents": ["view", "add"],
        "appointments": ["view"],
    },
}


def has_role_permission(user, module, action):

    if not user.is_authenticated:
        return False

    permissions = ROLE_PERMISSIONS.get(
        user.role,
        {},
    )

    if permissions.get("all"):
        return True

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

from django import forms
from .models import User


class UserRoleForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "role",
            "is_active",
        ]

        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control"}
            ),
            "role": forms.Select(
                attrs={"class": "form-control"}
            ),
        }