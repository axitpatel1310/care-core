from django.urls import path

from . import views


urlpatterns = [
    path("alerts/", views.alert_centre, name="alert_centre"),
    path("risk-register/", views.risk_register, name="resident_risk_register"),
    path("analytics/", views.analytics_dashboard, name="analytics_dashboard"),
    path("analytics/export/<slug:dataset>.csv", views.export_csv, name="analytics_export"),
    path("handover/", views.shift_handover, name="shift_handover"),
]
