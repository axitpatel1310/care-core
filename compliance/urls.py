from django.urls import path

from . import views


urlpatterns = [
    path("", views.compliance_dashboard, name="compliance_dashboard"),

    path("risks/", views.RiskList.as_view(), name="risk_list"),
    path("risks/add/", views.RiskCreate.as_view(), name="risk_create"),
    path("risks/<int:pk>/", views.RiskDetail.as_view(), name="risk_detail"),
    path("risks/<int:pk>/edit/", views.RiskUpdate.as_view(), name="risk_edit"),
    path("risks/<int:pk>/delete/", views.RiskDelete.as_view(), name="risk_delete"),

    path("documents/", views.DocumentList.as_view(), name="document_list"),
    path("documents/add/", views.DocumentCreate.as_view(), name="document_create"),
    path("documents/<int:pk>/", views.DocumentDetail.as_view(), name="document_detail"),
    path("documents/<int:pk>/download/", views.document_download, name="document_download"),
    path("documents/<int:pk>/edit/", views.DocumentUpdate.as_view(), name="document_edit"),
    path("documents/<int:pk>/delete/", views.DocumentDelete.as_view(), name="document_delete"),

    path("audits/", views.AuditList.as_view(), name="audit_list"),
    path("audits/add/", views.AuditCreate.as_view(), name="audit_create"),
    path("audits/<int:pk>/", views.AuditDetail.as_view(), name="audit_detail"),
    path("audits/<int:pk>/edit/", views.AuditUpdate.as_view(), name="audit_edit"),
    path("audits/<int:pk>/delete/", views.AuditDelete.as_view(), name="audit_delete"),
    path("audits/<int:audit_pk>/controls/add/", views.ControlCreate.as_view(), name="control_create"),
    path("controls/<int:pk>/edit/", views.ControlUpdate.as_view(), name="control_edit"),
    path("controls/<int:pk>/delete/", views.ControlDelete.as_view(), name="control_delete"),

    path("actions/", views.ActionList.as_view(), name="action_list"),
    path("actions/add/", views.ActionCreate.as_view(), name="action_create"),
    path("actions/<int:pk>/", views.ActionDetail.as_view(), name="corrective_action_detail"),
    path("actions/<int:pk>/edit/", views.ActionUpdate.as_view(), name="action_edit"),
    path("actions/<int:pk>/delete/", views.ActionDelete.as_view(), name="action_delete"),
]
