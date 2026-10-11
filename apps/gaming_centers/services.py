import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone as dt_timezone

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import HostApplication, HostRateBucket

HOST_RATE_LIMIT = 5
HOST_WINDOW_SECONDS = 900


class RateLimitExceeded(Exception):
    def __init__(self, retry_after):
        self.retry_after = retry_after


def _secret_hash(value):
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"), value.encode("utf-8"), hashlib.sha256
    ).hexdigest()


@transaction.atomic
def receive_host_application(validated_data, remote_addr):
    # Only REMOTE_ADDR is trusted: X-Forwarded-For must be normalized by a trusted edge first.
    key = _secret_hash(remote_addr or "unknown")
    now = timezone.now()
    hour_epoch = int(now.timestamp()) // 3600 * 3600
    replay_epoch = int(now.timestamp()) // HOST_WINDOW_SECONDS * HOST_WINDOW_SECONDS
    hour_start = datetime.fromtimestamp(hour_epoch, tz=dt_timezone.utc)
    replay_start = datetime.fromtimestamp(replay_epoch, tz=dt_timezone.utc)
    fingerprint = _secret_hash(json.dumps(validated_data, sort_keys=True, ensure_ascii=False))
    bucket, _ = HostRateBucket.objects.get_or_create(key=key, hour_start=hour_start)
    bucket = HostRateBucket.objects.select_for_update().get(pk=bucket.pk)
    previous = HostApplication.objects.filter(
        client_key=key, fingerprint=fingerprint, bucket_start=replay_start
    ).first()
    if previous:
        return previous
    if bucket.accepted_count >= HOST_RATE_LIMIT:
        raise RateLimitExceeded(max(1, 3600 - int(now.timestamp()) % 3600))
    application = HostApplication.objects.create(
        venue_name=validated_data["venueName"],
        manager_name=validated_data["managerName"],
        phone=validated_data["phone"],
        city=validated_data["city"],
        area=validated_data["area"],
        station_count=validated_data["stationCount"],
        games=validated_data["games"],
        description=validated_data["description"] or "",
        client_key=key,
        fingerprint=fingerprint,
        bucket_start=replay_start,
    )
    bucket.accepted_count += 1
    bucket.save(update_fields=["accepted_count"])
    return application


def host_retention_cutoff():
    # Operational owner B10 must arrange scheduled purge of expired private submissions.
    return timezone.now() - timedelta(days=180)
