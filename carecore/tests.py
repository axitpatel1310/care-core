import re
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import URLPattern, URLResolver, get_resolver

from accounts.models import User


def iter_patterns(resolver, prefix=""):

    for pattern in resolver.url_patterns:

        if isinstance(pattern, URLResolver):
            if str(pattern.pattern).startswith("admin"):
                continue
            yield from iter_patterns(pattern, prefix + str(pattern.pattern))

        elif isinstance(pattern, URLPattern):
            yield prefix + str(pattern.pattern), pattern.name


class PageSmokeTests(TestCase):
    """Render every GET page as every role against the demo data set: no page may error."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())

    def urls(self):

        for pattern, name in iter_patterns(get_resolver()):

            if "logout" in pattern or "media" in pattern or "(?P" in pattern:
                continue

            url = "/" + re.sub(r"<int:\w+>", "1", pattern)
            url = re.sub(r"<slug:\w+>", "incidents", url)

            yield url, name

    def test_every_page_renders_for_every_role(self):

        for email in (
            "admin@carecore.demo",
            "manager@carecore.demo",
            "rn@carecore.demo",
            "careworker@carecore.demo",
        ):
            self.client.force_login(User.objects.get(email=email))

            for url, name in self.urls():
                with self.subTest(user=email, url=url):
                    response = self.client.get(url)
                    self.assertIn(
                        response.status_code,
                        (200, 302, 403),
                        f"{name} returned {response.status_code}",
                    )

    def test_anonymous_users_are_redirected_to_login(self):

        for url, name in self.urls():

            if name in ("login", "register"):
                continue

            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/accounts/login/", response["Location"])

    def test_seed_demo_is_idempotent(self):

        counts = User.objects.count()
        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(User.objects.count(), counts)
