from django.urls import path
from . import views


urlpatterns = [
    path(
        "",
        views.compliance_dashboard,
        name="compliance_dashboard",
    ),
]