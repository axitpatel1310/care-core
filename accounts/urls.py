from django.urls import path

from . import views


urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path(
    "users/",
    views.user_management,
    name="user_management",
),

path(
    "users/<int:pk>/edit/",
    views.user_edit,
    name="user_edit",
),
path(
    "audit-log/",
    views.audit_log,
    name="audit_log",
),
]