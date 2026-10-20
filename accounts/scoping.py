"""
Facility-level data segregation.

Administrators see every facility. Everyone else sees residents in the
facility they work in (their staff profile) and any facility they manage.
Residents without a room yet (e.g. awaiting admission to a ward) are
visible to all staff so they are never orphaned.
"""

from django.db.models import Q

from staff.models import StaffMember


def visible_facility_ids(user):
    """Facility ids the user may see, or None for unrestricted access."""

    if user.is_superuser or getattr(user, "role", None) == "admin":
        return None

    cached = getattr(user, "_carecore_facility_ids", None)

    if cached is not None:
        return cached

    ids = set(
        StaffMember.objects
        .filter(user=user)
        .values_list("facility_id", flat=True)
    )
    ids.update(user.managed_facilities.values_list("id", flat=True))

    user._carecore_facility_ids = ids

    return ids


def resident_filter(user, prefix=""):
    """
    A Q object restricting a queryset to residents the user may see.
    `prefix` is the path to the resident, e.g. "resident__" for a care plan
    or "medication__resident__" for an administration record.
    """

    ids = visible_facility_ids(user)

    if ids is None:
        return Q()

    return (
        Q(**{f"{prefix}room__ward__facility__in": ids})
        | Q(**{f"{prefix}room__isnull": True})
    )


def scope(queryset, user, prefix="resident__"):
    """Filter any resident-linked queryset to the user's facilities."""

    return queryset.filter(resident_filter(user, prefix))


def scope_residents(queryset, user):
    return scope(queryset, user, prefix="")


def scope_staff(queryset, user):

    ids = visible_facility_ids(user)

    if ids is None:
        return queryset

    return queryset.filter(facility__in=ids)


def resident_path(model, depth=0):
    """
    The lookup path from `model` to a Resident ("" for Resident itself),
    or None when the model is not resident-linked (searched two hops deep).
    """

    from residents.models import Resident

    if model is Resident:
        return ""

    if depth > 1:
        return None

    for field in model._meta.concrete_fields:

        related = getattr(field, "related_model", None)

        if related is Resident:
            return f"{field.name}__"

    for field in model._meta.concrete_fields:

        related = getattr(field, "related_model", None)

        if related is not None and related is not model:

            inner = resident_path(related, depth + 1) if related._meta.app_label != "accounts" else None

            if inner:
                return f"{field.name}__{inner}"

    return None


def facility_path(model):

    from facility.models import Facility, Room, Ward

    return {
        Facility: "pk__in",
        Ward: "facility__in",
        Room: "ward__facility__in",
        StaffMember: "facility__in",
    }.get(model)


def scope_for_model(queryset, user):
    """Restrict any queryset to what the user's facilities allow."""

    ids = visible_facility_ids(user)

    if ids is None:
        return queryset

    path = facility_path(queryset.model)

    if path is not None:
        return queryset.filter(**{path: ids})

    path = resident_path(queryset.model)

    if path is not None:
        return queryset.filter(resident_filter(user, path))

    return queryset


def get_visible_object_or_404(user, klass, *args, **kwargs):
    """get_object_or_404 that also enforces facility scoping (404, not 403, to avoid leaking existence)."""

    from django.shortcuts import _get_queryset, get_object_or_404

    return get_object_or_404(
        scope_for_model(_get_queryset(klass), user),
        *args,
        **kwargs,
    )


def limit_resident_choices(form, user):
    """
    Only offer residents, staff, rooms, wards and facilities from the user's
    facilities in form dropdowns; submitting another id then fails validation.
    """

    for field in form.fields.values():

        queryset = getattr(field, "queryset", None)

        if queryset is not None:
            field.queryset = scope_for_model(queryset, user)
