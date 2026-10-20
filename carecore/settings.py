import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


DEBUG = env_bool("CARECORE_DEBUG", True)

# The fallback key is for local development only; production must set CARECORE_SECRET_KEY.
SECRET_KEY = os.environ.get(
    "CARECORE_SECRET_KEY",
    "django-insecure-dev-only-key-change-me" if DEBUG else None,
)

if not SECRET_KEY:
    raise RuntimeError("CARECORE_SECRET_KEY must be set when CARECORE_DEBUG is off.")

ALLOWED_HOSTS = env_list("CARECORE_ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else "")
CSRF_TRUSTED_ORIGINS = env_list("CARECORE_CSRF_TRUSTED_ORIGINS")
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

AUTHENTICATION_BACKENDS = [
    "accounts.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "facility",
    "residents",
    "staff",
    "care",
    "medications",
    "incidents",
    "compliance",
    "appointments",
    "observations",
    "insights",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "accounts.middleware.CurrentRequestMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "carecore.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "insights.context_processors.alerts",
            ],
        },
    },
]

WSGI_APPLICATION = "carecore.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        # SQLite is used in every environment; point CARECORE_DB_PATH at a persistent volume in Docker.
        "NAME": os.environ.get("CARECORE_DB_PATH", BASE_DIR / "db.sqlite3"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("CARECORE_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Uploaded files are not publicly served: they are streamed by permission-checked views.
MEDIA_ROOT = Path(os.environ.get("CARECORE_MEDIA_ROOT", BASE_DIR / "media"))

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

# Password-reset emails print to the console in development; set CARECORE_EMAIL_* for SMTP.
EMAIL_BACKEND = os.environ.get(
    "CARECORE_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.environ.get("CARECORE_EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("CARECORE_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("CARECORE_EMAIL_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("CARECORE_EMAIL_PASSWORD", "")
EMAIL_USE_TLS = env_bool("CARECORE_EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = os.environ.get("CARECORE_FROM_EMAIL", "CareCore <no-reply@carecore.local>")
PASSWORD_RESET_TIMEOUT = 60 * 60  # one hour

SESSION_COOKIE_AGE = 60 * 60 * 8  # one shift
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

if not DEBUG:
    SESSION_COOKIE_SECURE = env_bool("CARECORE_SECURE_COOKIES", True)
    CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
    SECURE_SSL_REDIRECT = env_bool("CARECORE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # Preloading is hard to undo, so it is opt-in per deployment.
    SECURE_HSTS_PRELOAD = env_bool("CARECORE_HSTS_PRELOAD", False)
    if not SECURE_HSTS_PRELOAD:
        SILENCED_SYSTEM_CHECKS = ["security.W021"]
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("CARECORE_LOG_LEVEL", "INFO"),
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
