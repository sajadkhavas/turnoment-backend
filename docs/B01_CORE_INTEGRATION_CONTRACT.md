# B01 Core Integration Contract — Issue #47

**Backend START_SHA:** 0f5d44646b608106ad20db97ec8c559fa084e6ce
**Frontend source:** sajadkhavas/turnoment at 1668109bae5ec7abb5e022e5857ffa65cc131501
**Scope:** B01 only. No business endpoint, finance, payment or P01 rewrite.

## Public import seams for B02–B10

- `apps.core.identifiers.public_id(value)`: strict ASCII [A-Za-z0-9_-] 1–128 public IDs, matching frozen frontend game/tournament/challenge keys; UUIDs use `uuid_public_id(uuid)` and remain UUID-form strings.
- `apps.core.api.views.CoreAPIView` / `CoreGenericAPIView`: opt-in error normalization; DRF default SessionAuthentication and IsAuthenticated remain inherited. Public views must **explicitly** set both `authentication_classes=[]` and `permission_classes=[AllowAny]` when appropriate.
- `apps.core.api.errors.error_response(code, message, status=..., fields=...)`: standard `{"error":{"code":"...","message":"...","fields":{...}}}` for explicit failures; nested `fields` is only included for validation. Unhandled exceptions remain 500, not a fake success.
- `apps.core.api.pagination.ContractPagination`: opt-in `schemaVersion:1, items, pagination:{currentPage,totalPages,totalItems,pageSize}`, query `page` and `pageSize` (1–100). Frozen frontend projections vary: e.g. game catalog is an **unpaginated** `schemaVersion/totalItems/items` projection; challenge empty-state `totalPages=0`. Domains must match their exact frontend Zod schema and must **not** blindly use the core paginator for those shapes.
- `apps.audit.services.emit_event(source, event_type, subject_type, subject_id, idempotency_key, payload)`: returns (DomainEvent, created); DB UniqueConstraint(source,idempotency_key), mismatch raises IdempotencyConflict. Record in same outer `transaction.atomic()` as domain truth. Events are durable **pending integration signals**, not delivered notifications. No automatic Celery dispatch, consumer, acknowledgment, or HTTP read endpoint.
- `apps.audit.services.record_audit(source, action, subject_type, subject_id, idempotency_key, actor=None, details=None)`: returns (AuditRecord, created); private actor FK, idempotent key with collision detection. Records are application-managed append-only in normal service use; they are **not** database tamper-proof.
- Event/audit JSON objects are max 16 KiB and reject sensitive key names, non-JSON payloads and NaNs. Never include tokens, private identity or secrets even under different key names.
- `apps.core.testing.session_client(user, enforce_csrf_checks=True)` plus `assert_contract_error` for test reuse. `force_login` maintains normal session auth rather than `force_authenticate`.

## Lifecycle and integration ownership

B08 emits `match.finalized` from the same transaction as finalized match truth; B09 consumes keyed events exactly once using its **own durable consumer offset/idempotency constraint** (not B01's producer constraint alone). B10 owns delivery/operations, B99 owns dispatcher/consumer registration, polling/locking/retries and cross-domain wiring. No other domain models imported in B01.

Core error and pagination helpers are intentionally **opt-in**: changing the global DRF exception handler or pagination would break frozen P01 validation shapes and other untouched routes. B99 must reconcile per-endpoint response shapes when integrating the frontend.

## Shared configuration changes

Only `config/settings/base.py`: register core/audit apps. `apps.core.frontend.FROZEN_FRONTEND_CONTRACT_SHA` pins the accepted B00 frontend SHA. The legacy P00 `/api/v1/system/meta/` baseline setting (and its CI expectation) is intentionally preserved because changing it breaks the frozen P00 health contract/test outside B01 ownership; B99 must authorize any subsequent meta endpoint migration. No shared CI, root dependencies, authentication, permission defaults, server URLs or CI steps changed.

## Official technical references and decisions

- Django transactions: https://docs.djangoproject.com/en/6.0/topics/db/transactions/ — outer service transaction commits event and domain state atomically; rollback tested.
- Django constraints: https://docs.djangoproject.com/en/6.0/ref/models/constraints/ — database unique and nonblank event/action constraints guard direct ORM writes and concurrent duplicate keys.
- DRF exceptions: https://www.django-rest-framework.org/api-guide/exceptions/ — custom exception handler integrates with DRF's existing classification; do not wrap arbitrary failures as success.
- DRF pagination: https://www.django-rest-framework.org/api-guide/pagination/ — opt-in paginator on GenericAPIView; project exact frontend page shapes.
- DRF authentication: https://www.django-rest-framework.org/api-guide/authentication/ — SessionAuthentication and CSRF stay authoritative.
- DRF permissions: https://www.django-rest-framework.org/api-guide/permissions/ — object permissions are owned by domain services/querysets.
- Celery tasks: https://docs.celeryq.dev/en/stable/userguide/tasks.html — eventual delivery is distinct from durable transaction truth.

## Financial exclusion

FINANCIAL EXECUTION ADDED: NO
