from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from django.db import IntegrityError, connections, transaction
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from apps.audit.models import AuditRecord, DomainEvent
from apps.audit.services import IdempotencyConflict, emit_event, record_audit


ARGS = dict(
    source="matches", event_type="match.finalized", subject_type="match",
    subject_id="match_123", idempotency_key="matchfinal_12345678",
    payload={"result": {"winnerId": "player_123"}},
)


@pytest.mark.django_db
def test_event_is_durable_idempotent_and_conflicts_fail_closed():
    first, created = emit_event(**ARGS)
    assert created is True
    repeat, created = emit_event(**ARGS)
    assert created is False
    assert repeat.pk == first.pk
    assert DomainEvent.objects.count() == 1
    with pytest.raises(IdempotencyConflict):
        emit_event(**{**ARGS, "payload": {"result": {"winnerId": "player_999"}}})
    assert DomainEvent.objects.count() == 1


@pytest.mark.django_db
def test_audit_actor_is_private_and_replay_safe():
    user = User.objects.create_user(phone="09121234567")
    args = dict(
        source="matches", action="match.confirmed", subject_type="match",
        subject_id="match_123", idempotency_key="auditmatch_12345678",
        actor=user, details={"state": "confirmed"},
    )
    first, created = record_audit(**args)
    assert created is True
    second, created = record_audit(**args)
    assert created is False
    assert second.id == first.id
    assert first.actor_id == user.pk
    with pytest.raises(IdempotencyConflict):
        record_audit(**{**args, "details": {"state": "cancelled"}})
    assert AuditRecord.objects.count() == 1


@pytest.mark.django_db
def test_payload_rejects_private_or_non_json_and_bad_identifier():
    bad_payloads = [{"phone": "x"}, {"inner": [{"token": "x"}]}, {"nan": float("nan")},
                    {"bad": set([1])}, {"big": "x" * 17000}]
    for payload in bad_payloads:
        with pytest.raises(ValueError):
            emit_event(**{**ARGS, "payload": payload})
    with pytest.raises(ValidationError):
        emit_event(**{**ARGS, "subject_id": "match/1"})
    with pytest.raises(ValueError):
        emit_event(**{**ARGS, "idempotency_key": "short"})
    assert DomainEvent.objects.count() == 0


@pytest.mark.django_db
def test_database_uniqueness_and_nonempty_event_type():
    emit_event(**ARGS)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            DomainEvent.objects.create(
                source=ARGS["source"], idempotency_key=ARGS["idempotency_key"],
                event_type="match.other", subject_type="match", subject_id="match_123",
            )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            DomainEvent.objects.create(
                source="results", idempotency_key="otherkey123",
                event_type="", subject_type="match", subject_id="match_123",
            )


@pytest.mark.django_db
def test_atomic_rollback_removes_event_and_audit():
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            emit_event(**ARGS)
            record_audit(
                source="matches", action="match.finished", subject_type="match",
                subject_id="match_123", idempotency_key="auditfinished_12345678",
            )
            raise RuntimeError("owning domain rolled back")
    assert DomainEvent.objects.count() == 0
    assert AuditRecord.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_parallel_same_event_key_produces_exactly_one_row():
    def worker():
        connections.close_all()
        try:
            return emit_event(**ARGS)[1]
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: worker(), range(2)))
    assert sorted(results) == [False, True]
    assert DomainEvent.objects.count() == 1


@pytest.mark.django_db
def test_audit_uniqueness_at_database_boundary():
    record_audit(
        source="results", action="result.created", subject_type="match",
        subject_id="match_1", idempotency_key="auditresult_12345",
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            AuditRecord.objects.create(
                source="results", action="result.changed", subject_type="match",
                subject_id="match_1", idempotency_key="auditresult_12345",
            )
