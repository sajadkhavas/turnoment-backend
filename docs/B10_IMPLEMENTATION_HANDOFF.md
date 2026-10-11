# B10 — Notifications / Moderation / Admin Operations

**Branch:** phase/b10-notifications-moderation-admin
**Backend baseline:** 0f5d44646b608106ad20db97ec8c559fa084e6ce
**Frozen frontend:** sajadkhavas/turnoment@1668109bae5ec7abb5e022e5857ffa65cc131501
**Issue:** #56

## Invariants and scope

- Notification list/read/read-all match frozen F10 JSON shape, including outcome wrappers, 5-item pages, read-state filtering and typed (never arbitrary-URL) targets.
- Notifications have unique (recipient, event_key); replay with conflicting content is rejected.
- All notification mutations lock the recipient row, keeping read commands/replay serializable against emission and other reads on PostgreSQL.
- Moderation references are unique (source_type, source_id); they do not mirror or mutate B04/B08 business state. Their ingestion is a narrow synchronous service call after owning transactions commit.
- Only P01 active is_staff+is_superuser accounts are platform operators. Center staff and ordinary staff, including is_staff without superuser, cannot access platform moderation API or Django admin. Later named operator delegation requires an explicit permission-model revision.
- State transitions: open -> in_review -> closed; a repeated transition is a no-op and never appends duplicate audit; audit decisions cannot be changed in admin.
- Celery is not invoked for committed notification or moderation truth. Delivery workers (if later connected) are side effects only.

## Shared wiring (integration owner review)

- config/settings/base.py: substitute custom Django admin config, register apps.notifications/apps.moderation.
- config/urls.py: include notifications and moderation v1 URL modules.
- No changes to P01 auth, dependencies, CI, other apps, phase registry or financial code.

## Interfaces awaiting integration

- B04: call `record_moderation_case(source_type="host_application", source_id=<receipt-id>, title=<safe-title>, center_id=<opaque-id-or-empty>)` after durable submission. Do not echo contact details in titles.
- B08: call `record_moderation_case(source_type="dispute", source_id=<dispute-id>, title=<safe-title>, center_id=<opaque-id-or-empty>)` after the owning transaction; do not write dispute outcome through moderation.
- Managed-content owner: same seam with `source_type="managed_content"`; source IDs are opaque route-safe tokens.
- B04/B08/B05/B07/B02: after their event is committed, call `emit_notification(recipient_id, event_key, kind, title, body, target_kind, target_id)` with durable stable event key. Do not dispatch Celery as substitute for this DB projection. Consumers must authorize target APIs separately.
- External domain models not present on B10 baseline: no fake host/dispute tables or fabricated results introduced.

## Official references

- Django 6.1 admin site override: https://docs.djangoproject.com/en/6.1/ref/contrib/admin/#overriding-the-default-admin-site
- Django 6.1 constraints: https://docs.djangoproject.com/en/6.1/ref/models/constraints/
- Django transactions: https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- Django select_for_update: https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update
- DRF SessionAuthentication/CSRF: https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication
- DRF permissions: https://www.django-rest-framework.org/api-guide/permissions/
- PostgreSQL locking: https://www.postgresql.org/docs/current/explicit-locking.html

FINANCIAL EXECUTION ADDED: NO
