from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections

from apps.accounts.models import User
from apps.registrations.models import Registration
from apps.registrations.services import register
from apps.tournaments.tests.test_b05 import make_tournament, payload


@pytest.mark.django_db(transaction=True)
def test_two_players_racing_for_last_slot_only_one_confirms():
    t = make_tournament(capacity=1)
    a = User.objects.create_user(phone="09129876541")
    b = User.objects.create_user(phone="09129876542")
    barrier = Barrier(2)

    def attempt(user):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return register(identifier=str(t.pk), user=user, payload=payload())
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, [a, b]))
    assert sorted(item["outcome"] for item in results) == ["confirmed", "unavailable"]
    t.refresh_from_db()
    assert t.registered_count == 1
    assert Registration.objects.filter(tournament=t).count() == 1


@pytest.mark.django_db(transaction=True)
def test_same_player_concurrent_duplicate_is_idempotent():
    t = make_tournament(capacity=2)
    a = User.objects.create_user(phone="09129876543")
    barrier = Barrier(2)

    def attempt(_):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return register(identifier=str(t.pk), user=a, payload=payload())
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, range(2)))
    assert {item["outcome"] for item in results} == {
        "confirmed", "already_registered"
    }
    t.refresh_from_db()
    assert t.registered_count == 1
    assert Registration.objects.filter(tournament=t, user=a).count() == 1
