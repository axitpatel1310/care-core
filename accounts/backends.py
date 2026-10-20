from django.contrib.auth.backends import ModelBackend

from .models import User


class EmailBackend(ModelBackend):
    """Authenticate with the account email address instead of the username."""

    def authenticate(self, request, username=None, password=None, **kwargs):

        email = kwargs.get("email", username)

        if not email or password is None:
            return None

        user = User.objects.filter(email__iexact=email.strip()).first()

        if user is None:
            # Run the hasher anyway to keep response timing uniform.
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
