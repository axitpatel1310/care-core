from django.urls import path
from . import views

urlpatterns = [

    path(
        "",
        views.incident_list,
        name="incident_list",
    ),

    path(
        "add/",
        views.incident_create,
        name="incident_create",
    ),

    path(
        "<int:pk>/",
        views.incident_detail,
        name="incident_detail",
    ),
    path(
    "<int:pk>/investigate/",
    views.incident_investigate,
    name="incident_investigate",
),

    path(
        "<int:pk>/edit/",
        views.incident_edit,
        name="incident_edit",
    ),

    path(
        "<int:pk>/resolve/",
        views.incident_resolve,
        name="incident_resolve",
    ),

    path(
        "<int:pk>/delete/",
        views.incident_delete,
        name="incident_delete",
    ),

]
