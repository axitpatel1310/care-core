from django.contrib import admin
from django.urls import include, path

from .views import dashboard


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard, name="dashboard"),
    path("residents/",include("residents.urls"),),
        path(
        "accounts/",
        include("accounts.urls"),
    ),
    path(
        "facility/",
        include("facility.urls"),
    ),
    path(
        "care/",
        include("care.urls"),
    ),
    path(
        "staff/",
        include("staff.urls"),
    ),
    path(
        "incidents/",
        include("incidents.urls"),
    ),
    path(
        "compliance/",
        include("compliance.urls"),
    ),
    path(
        "medications/",
        include("medications.urls"),
    ),
    path(
       "appointments/",
        include("appointments.urls"),
    ),
]