from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.staff_list,
        name="staff_list",
    ),

    path(
        "add/",
        views.staff_create,
        name="staff_create",
    ),

    path(
        "<int:pk>/",
        views.staff_detail,
        name="staff_detail",
    ),

    path(
        "<int:pk>/edit/",
        views.staff_edit,
        name="staff_edit",
    ),

    path(
        "<int:pk>/delete/",
        views.staff_delete,
        name="staff_delete",
    ),
    path(
    "assignments/",
    views.assignment_list,
    name="assignment_list",
),

path(
    "assignments/add/",
    views.assignment_create,
    name="assignment_create",
),

path(
    "assignments/<int:pk>/",
    views.assignment_detail,
    name="assignment_detail",
),

path(
    "assignments/<int:pk>/edit/",
    views.assignment_edit,
    name="assignment_edit",
),

path(
    "assignments/<int:pk>/delete/",
    views.assignment_delete,
    name="assignment_delete",
),
path(
    "workspace/",
    views.staff_workspace,
    name="staff_workspace",
),
]