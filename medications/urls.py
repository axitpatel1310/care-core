from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.medication_list,
        name="medication_list",
    ),

    path(
        "add/",
        views.medication_create,
        name="medication_create",
    ),

    path(
        "<int:pk>/",
        views.medication_detail,
        name="medication_detail",
    ),

    path(
        "<int:pk>/edit/",
        views.medication_edit,
        name="medication_edit",
    ),

    path(
        "<int:pk>/delete/",
        views.medication_delete,
        name="medication_delete",
    ),
    path(
        "administrations/",
        views.administration_list,
        name="administration_list",
    ),
    path(
        "<int:medication_id>/administrations/add/",
        views.administration_create,
        name="administration_create",
    ),
    path(
        "administrations/<int:pk>/",
        views.administration_detail,
        name="administration_detail",
    ),

    path(
        "administrations/<int:pk>/edit/",
        views.administration_edit,
        name="administration_edit",
    ),

    path(
        "administrations/<int:pk>/delete/",
        views.administration_delete,
        name="administration_delete",
    ),
    path(
        "<int:medication_pk>/history/",
        views.administration_history,
        name="administration_history",
    ),
        path(
        "<int:medication_id>/administrations/",
        views.medication_administration_history,
        name="medication_administration_history",
    ),

    path(
        "due-today/",
        views.medication_due_today,
        name="medication_due_today",
    ),

]