from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.observation_list,
        name="observation_list",
    ),

    path(
        "add/",
        views.observation_create,
        name="observation_create",
    ),

    path(
        "<int:pk>/",
        views.observation_detail,
        name="observation_detail",
    ),

    path(
        "<int:pk>/delete/",
        views.observation_delete,
        name="observation_delete",
    ),

    path(
        "resident/<int:resident_pk>/",
        views.resident_observations,
        name="resident_observations",
    ),

]
