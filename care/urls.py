from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.care_plan_list,
        name="care_plan_list",
    ),

    path(
        "add/",
        views.care_plan_create,
        name="care_plan_create",
    ),

    path(
        "<int:pk>/",
        views.care_plan_detail,
        name="care_plan_detail",
    ),

    path(
        "<int:pk>/edit/",
        views.care_plan_edit,
        name="care_plan_edit",
    ),

    path(
        "<int:pk>/delete/",
        views.care_plan_delete,
        name="care_plan_delete",
    ),
    path(
    "assessments/",
    views.assessment_list,
    name="assessment_list",
    ),
    path(
        "assessments/add/",
        views.assessment_create,
        name="assessment_create",
    ),

    path(
        "assessments/<int:pk>/",
        views.assessment_detail,
        name="assessment_detail",
    ),

    path(
        "assessments/<int:pk>/edit/",
        views.assessment_edit,
        name="assessment_edit",
    ),

    path(
        "assessments/<int:pk>/delete/",
        views.assessment_delete,
        name="assessment_delete",
    ),
    path(
    "behavioural-support/",
    views.behavioural_support_list,
    name="behavioural_support_list",
),

path(
    "behavioural-support/add/",
    views.behavioural_support_create,
    name="behavioural_support_create",
),

path(
    "behavioural-support/<int:pk>/",
    views.behavioural_support_detail,
    name="behavioural_support_detail",
),

path(
    "behavioural-support/<int:pk>/edit/",
    views.behavioural_support_edit,
    name="behavioural_support_edit",
),

path(
    "behavioural-support/<int:pk>/delete/",
    views.behavioural_support_delete,
    name="behavioural_support_delete",
),
    path(
        "tasks/",
        views.task_list,
        name="task_list",
    ),

    path(
        "tasks/add/",
        views.task_create,
        name="task_create",
    ),

    path(
        "tasks/<int:pk>/",
        views.task_detail,
        name="task_detail",
    ),

    path(
        "tasks/<int:pk>/edit/",
        views.task_edit,
        name="task_edit",
    ),

    path(
        "tasks/<int:pk>/complete/",
        views.task_complete,
        name="task_complete",
    ),

    path(
        "tasks/<int:pk>/start/",
        views.task_start,
        name="task_start",
    ),

    path(
        "tasks/<int:pk>/cancel/",
        views.task_cancel,
        name="task_cancel",
    ),

    path(
        "tasks/<int:pk>/delete/",
        views.task_delete,
        name="task_delete",
    ),

]