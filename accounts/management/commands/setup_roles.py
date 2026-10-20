from django.core.management.base import BaseCommand

from accounts.models import User
from accounts.roles import (
    configure_role_groups,
    sync_user_role_group,
)


class Command(BaseCommand):

    help = "Create and configure CareCore role groups."

    def handle(self, *args, **options):

        configure_role_groups(
            log=lambda message: self.stdout.write(
                self.style.SUCCESS(message)
            ),
        )

        for user in User.objects.all():
            sync_user_role_group(user)

        self.stdout.write(
            self.style.SUCCESS(
                "Synchronised user role groups."
            )
        )
