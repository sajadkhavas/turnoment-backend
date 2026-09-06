import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ImproperlyConfigured(f"Required environment variable is missing: {name}")
    return value


DEBUG = False
SECRET_KEY = required_env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = csv_env("DJANGO_ALLOWED_HOSTS")  # noqa: F405
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must contain at least one host")

CSRF_TRUSTED_ORIGINS = csv_env("DJANGO_CSRF_TRUSTED_ORIGINS")  # noqa: F405

DATABASES["default"].update(  # noqa: F405
    {
        "NAME": required_env("DB_NAME"),
        "USER": required_env("DB_USER"),
        "PASSWORD": required_env("DB_PASSWORD"),
        "HOST": required_env("DB_HOST"),
        "PORT": required_env("DB_PORT"),
    }
)

REDIS_URL = required_env("REDIS_URL")
CACHES["default"]["LOCATION"] = REDIS_URL  # noqa: F405
CELERY_BROKER_URL = required_env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = required_env("CELERY_RESULT_BACKEND")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS preload is intentionally deferred until the real production domains are final,
# HTTPS-only coverage for every subdomain is verified, and preload enrollment is an
# explicit deployment decision. Keep every other deployment warning fatal in CI.
SILENCED_SYSTEM_CHECKS = ["security.W021"]
