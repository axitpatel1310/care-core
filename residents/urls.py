from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.resident_list,
        name="resident_list",
    ),

    path(
        "add/",
        views.resident_create,
        name="resident_create",
    ),

    path(
        "<int:pk>/",
        views.resident_detail,
        name="resident_detail",
    ),

    path(
        "<int:pk>/edit/",
        views.resident_edit,
        name="resident_edit",
    ),

    path(
        "<int:pk>/delete/",
        views.resident_delete,
        name="resident_delete",
    ),
    path(
    "<int:resident_pk>/contacts/add/",
    views.contact_create,
    name="contact_create",
),

path(
    "contacts/<int:pk>/",
    views.contact_detail,
    name="contact_detail",
),

path(
    "contacts/<int:pk>/edit/",
    views.contact_edit,
    name="contact_edit",
),

path(
    "contacts/<int:pk>/delete/",
    views.contact_delete,
    name="contact_delete",
),
]