from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.facility_list,
        name="facility_list",
    ),

    path(
        "add/",
        views.facility_create,
        name="facility_create",
    ),

    path(
        "<int:pk>/",
        views.facility_detail,
        name="facility_detail",
    ),

    path(
        "<int:pk>/edit/",
        views.facility_edit,
        name="facility_edit",
    ),

    path(
        "<int:pk>/delete/",
        views.facility_delete,
        name="facility_delete",
    ),


    # Wards

    path(
        "wards/add/",
        views.ward_create,
        name="ward_create",
    ),

    path(
        "wards/<int:pk>/edit/",
        views.ward_edit,
        name="ward_edit",
    ),

    path(
        "wards/<int:pk>/delete/",
        views.ward_delete,
        name="ward_delete",
    ),


    # Rooms

    path(
        "rooms/add/",
        views.room_create,
        name="room_create",
    ),

    path(
        "rooms/<int:pk>/edit/",
        views.room_edit,
        name="room_edit",
    ),

    path(
        "rooms/<int:pk>/delete/",
        views.room_delete,
        name="room_delete",
    ),
]