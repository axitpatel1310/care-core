from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):

        from django.apps import apps

        from . import audit_trail, signals

        audit_trail.connect(apps)

        # Runs after every app has migrated, so all permissions exist.
        post_migrate.connect(
            signals.setup_role_groups,
            dispatch_uid="carecore_setup_role_groups",
        )
