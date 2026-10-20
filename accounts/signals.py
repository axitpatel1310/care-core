from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User
from .roles import configure_role_groups, sync_user_role_group


@receiver(post_save, sender=User)
def assign_role_group(sender, instance, raw=False, **kwargs):

    if raw:
        return

    sync_user_role_group(instance)


def setup_role_groups(sender, **kwargs):

    configure_role_groups()
