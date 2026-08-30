from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.appointment_list,
        name="appointment_list",
    ),

    path(
        "add/",
        views.appointment_create,
        name="appointment_create",
    ),

    path(
        "<int:pk>/",
        views.appointment_detail,
        name="appointment_detail",
    ),

    path(
        "<int:pk>/edit/",
        views.appointment_edit,
        name="appointment_edit",
    ),

    path(
        "<int:pk>/delete/",
        views.appointment_delete,
        name="appointment_delete",
    ),

]