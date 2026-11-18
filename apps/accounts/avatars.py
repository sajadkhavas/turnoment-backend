import re

from django.conf import settings


def profile_avatar(key):
    if re.fullmatch(r"/api/v1/media/photos/[a-fA-F0-9-]{36}/image/", key):
        return key
    if re.fullmatch(r"players/(?:[\w-]+/)*[\w.-]+\.(?:webp|png|jpe?g|avif)", key, re.ASCII):
        media_url = settings.MEDIA_URL or "/media/"
        if media_url.startswith("/") and not media_url.startswith("//"):
            return media_url.rstrip("/") + "/" + key
    return None
