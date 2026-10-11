# Official Source Audit

Each implementation phase records the upstream documentation reviewed before and during implementation.

## P00 — Backend Foundation

Reviewed 2026-09-06.

### Django 6.1

- Release notes / Python compatibility: https://docs.djangoproject.com/en/6.1/releases/6.1/
- Installation FAQ / production PostgreSQL recommendation: https://docs.djangoproject.com/en/6.1/faq/install/
- Database support and PostgreSQL notes: https://docs.djangoproject.com/en/6.1/ref/databases/
- Deployment checklist: https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/
- Settings reference: https://docs.djangoproject.com/en/6.1/ref/settings/
- Security system checks: https://docs.djangoproject.com/en/6.1/ref/checks/#security

Decisions:

- Support Python 3.12–3.14, matching Django 6.1.
- PostgreSQL is the durable database; Django 6.1 supports PostgreSQL 15+ and recommends psycopg 3.
- Keep `CONN_MAX_AGE=0` under ASGI baseline; Django docs advise disabling persistent connections for ASGI and considering backend pooling if needed.
- Production secrets are environment-only and production config fails closed.
- CI includes Django deployment checks with warnings treated as failures.
- `security.W021` is the only deliberately silenced deployment check at P00. HSTS itself remains enabled for one year with subdomains, but preload enrollment is deferred until the real production domains and HTTPS coverage of every relevant subdomain are verified. All other deployment warnings remain fatal.

### Django REST Framework 3.18

- Release notes: https://www.django-rest-framework.org/community/release-notes/

Decisions:

- Use DRF 3.18 because it explicitly adds Django 6.1 support.
- Global API policy defaults to authenticated; individual public read/health endpoints explicitly allow anonymous access.

### Celery 5.6

- Django integration: https://docs.celeryq.dev/en/stable/django/

Decision:

- Celery is the initial background-job framework. Transaction-critical truth remains synchronous; async jobs handle notifications, external IO, derived projections and other retryable work.

### Redis

- redis-py guide: https://redis.io/docs/latest/develop/clients/redis-py/
- Production usage: https://redis.io/docs/latest/develop/clients/redis-py/produsage/

Decision:

- Use redis-py through Django/queue integrations; production hardening includes timeouts, health checks, exception handling and appropriate secure connectivity.

### PostgreSQL

- Explicit locking: https://www.postgresql.org/docs/current/explicit-locking.html

Decision:

- Race-prone domain transitions use database constraints and explicit locking only where the domain requires it.

---

## P01 — Accounts, Player Identity & Authentication Foundation

Reviewed 2026-09-06 before implementation and re-reviewed before closeout.

### Django custom users / authentication

- Customizing authentication / custom user model: https://docs.djangoproject.com/en/6.1/topics/auth/customizing/
- Authentication in web requests, `login()` and `logout()`: https://docs.djangoproject.com/en/6.1/topics/auth/default/
- Sessions: https://docs.djangoproject.com/en/6.1/topics/http/sessions/
- CSRF protection: https://docs.djangoproject.com/en/6.1/howto/csrf/
- Settings reference for CSRF/session cookies: https://docs.djangoproject.com/en/6.1/ref/settings/

Decisions:

- Establish `AUTH_USER_MODEL` now, before durable product migrations depend on Django's default user model. Django documents that changing the user model later is complex and requires manual schema/data work, and that the custom user model must be created in the first migration of its app.
- Phone is the login identifier; passwords remain available only for administrative/superuser access. OTP-created player accounts receive an unusable password.
- Web authentication uses Django sessions. Login establishes the authenticated session through Django's `login()` and logout uses Django's `logout()`.
- Anonymous OTP write endpoints are explicitly CSRF-protected. A bootstrap endpoint forces issuance of the CSRF cookie/token for the same-origin TanStack web client, matching Django's documented `ensure_csrf_cookie()` pattern when a page does not render `{% csrf_token %}`.
- The client must send `X-CSRFToken` for unsafe same-origin requests. Production session and CSRF cookies remain Secure; the session cookie remains HttpOnly.

### Django REST Framework

- Authentication: https://www.django-rest-framework.org/api-guide/authentication/
- Permissions: https://www.django-rest-framework.org/api-guide/permissions/
- Throttling: https://www.django-rest-framework.org/api-guide/throttling/
- Testing / CSRF flow: https://www.django-rest-framework.org/api-guide/testing/
- AJAX / CSRF / CORS guidance: https://www.django-rest-framework.org/topics/ajax-csrf-cors/

Decisions:

- Authenticated account endpoints use DRF `SessionAuthentication` plus `IsAuthenticated`.
- OTP/bootstrap/public-player endpoints explicitly use `AllowAny`; they do not inherit anonymous access accidentally.
- Same-session AJAX use aligns with DRF guidance for `SessionAuthentication`, and unsafe requests require a valid CSRF token.
- The test suite follows the documented browser-like CSRF flow: obtain a token/cookie first, then send it for unsafe writes.
- DRF throttling is not treated as the security boundary for OTP abuse. DRF explicitly documents that application-level throttling is not a brute-force/DDoS security control and that built-in cache-backed throttles can be fuzzy under concurrency. OTP cooldown/request-window state is therefore persisted in PostgreSQL and updated transactionally; edge/network rate limiting remains an additional deployment concern.

### PostgreSQL / Django transactions

- Django transactions: https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- `select_for_update()`: https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update
- PostgreSQL explicit locking: https://www.postgresql.org/docs/current/explicit-locking.html

Decisions:

- OTP request-state and OTP verification transitions use transactions and row-level locking where concurrent mutation matters.
- Incorrect-attempt decrement, expiry consumption and successful single-use consumption are persisted before domain errors are returned; exceptions are not raised in a way that rolls those state changes back.
- Issuing a new login challenge invalidates earlier unconsumed challenges for that phone so only the latest delivered OTP can authenticate.
- Failed OTP delivery marks the undelivered challenge consumed and restores request-state quota/cooldown instead of penalizing the user for provider failure.

### Privacy / identity contract

Decision:

- `User` holds private account identity; `PlayerProfile` holds public competitive identity. Public player serialization never exposes phone, email, permissions or interview opt-in state.
- Persistent venue roles are not flattened into account booleans; venue-scoped memberships belong to the gaming-center domain in a later phase.

### Closeout verification

Re-reviewed 2026-09-06 after implementation and before freeze against the official Django 6.1 and DRF documentation above. No architecture deviation or source conflict was found. The P01 implementation remains aligned with the documented custom-user timing requirement, Django session/CSRF behavior, DRF same-session AJAX guidance, and DRF's warning not to use application throttling as a brute-force security boundary.
---

## B01 — Core Contract & Integration Foundation

Reviewed 2026-10-11 for Issue #47 / PR #59 against frontend contract `1668109bae5ec7abb5e022e5857ffa65cc131501`.

### Django 6.1 / PostgreSQL transaction and constraint primitives

- Transactions and nested `atomic()`: https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- Model constraints: https://docs.djangoproject.com/en/6.1/ref/models/constraints/
- PostgreSQL explicit locking: https://www.postgresql.org/docs/current/explicit-locking.html

Decisions:

- Producers record a durable domain event in the same outer transaction as the authoritative business transition. Nested `atomic()` does not independently commit an event while the owner rolls back.
- PostgreSQL uniqueness on `(source, idempotency_key)` prevents duplicate event/audit rows under concurrent insertion. Nonempty event type/action constraints are database enforced.
- B01 does not claim consumer delivery or immutable/tamper-proof audit storage; B99/B10 own dispatcher operations, and B09 owns per-consumer idempotency.

### Django REST Framework

- Exceptions: https://www.django-rest-framework.org/api-guide/exceptions/
- Pagination: https://www.django-rest-framework.org/api-guide/pagination/
- Authentication: https://www.django-rest-framework.org/api-guide/authentication/
- Permissions: https://www.django-rest-framework.org/api-guide/permissions/

Decisions:

- Core exception/pagination helpers are opt-in, not global, to preserve the accepted P01 authentication/response contract.
- Keep inherited `SessionAuthentication` and `IsAuthenticated` for private APIs. Public routes must make their authentication and permission policies explicit.
- Domain serializers and output projections must match each precise frontend contract rather than automatically applying one paginator to every endpoint.

### Celery

- Task and retry semantics: https://docs.celeryq.dev/en/stable/userguide/tasks.html

Decision:

- Enqueuing a database outbox row is not notification delivery; publication, retry handling, offsets, and recovery are integration work. Do not publish transaction-sensitive side effects before commit.

Financial execution remains explicitly excluded from B01.
---

## B03 — Games / Rules / Public Discovery

Reviewed 2026-10-11 for Issue #49 and PR #60, frontend contract `1668109bae5ec7abb5e022e5857ffa65cc131501`.

### Django / PostgreSQL

- Constraints and uniqueness: https://docs.djangoproject.com/en/6.1/ref/models/constraints/
- PostgreSQL text search: https://docs.djangoproject.com/en/6.1/ref/contrib/postgres/search/
- GIN indexes: https://docs.djangoproject.com/en/6.1/ref/contrib/postgres/indexes/
- Database migrations: https://docs.djangoproject.com/en/6.1/topics/migrations/
- PostgreSQL locking and concurrent writes: https://www.postgresql.org/docs/current/explicit-locking.html

Decisions:
- Published games and policy revisions are served from PostgreSQL rather than mock fixtures.
- Stable game IDs and slugs are unique. `games_public_search_idx` indexes text search; relational consumers use game PK, not display labels.
- `Ruleset` is versioned policy text; only one published revision per key is permitted using a partial unique constraint.
- A maximum of 100 catalog items matches the frozen v1 frontend contract. Overflow returns explicit 503 until a separately approved pagination contract exists.
- Tournament/center/ranking counts and projections require B04/B05/B09 authoritative data, not fabricated values. Their B03 integration seams remain a tracked B99 responsibility.

### DRF

- Authentication: https://www.django-rest-framework.org/api-guide/authentication/
- Permissions: https://www.django-rest-framework.org/api-guide/permissions/
- APIViews: https://www.django-rest-framework.org/api-guide/views/
- Validation: https://www.django-rest-framework.org/api-guide/serializers/

Decisions:
- Public catalog/detail/rules/discovery endpoints explicitly set `AllowAny`; they offer GET only and preserve private P01 defaults.
- Read projections must match the exact frontend schema; games do not own tournament registration, center staff or ranked-match decisions.
- Financial execution added: NO.

---

## B04 — Gaming Centers / Host / Resources

Reviewed 2026-10-11 against the frozen frontend contract
`sajadkhavas/turnoment@1668109bae5ec7abb5e022e5857ffa65cc131501`.

- Django constraints: https://docs.djangoproject.com/en/6.1/ref/models/constraints/
- Django transactions: https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- Django select_for_update: https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update
- DRF authentication: https://www.django-rest-framework.org/api-guide/authentication/
- DRF permissions: https://www.django-rest-framework.org/api-guide/permissions/
- DRF serializers: https://www.django-rest-framework.org/api-guide/serializers/
- DRF throttling: https://www.django-rest-framework.org/api-guide/throttling/

Decisions: center scope is checked per object, with no mapping to Django is_staff.
Anonymous acquisition uses an explicit no-session authentication policy to avoid cookie-dependent
CSRF behavior, with persistent transactional hourly admission buckets. DB constraints protect
repeat memberships, station codes, resource labels, duplicate host submissions and public gallery
positions. Rate buckets use row locks; duplicate identical 15-minute submissions return the same
receipt. DRF cache throttles are not represented as complete abuse/DoS prevention. Public
visibility requires publication and explicit contact/address/map consent. Financial execution is
not implemented; B05 and B10 integration seams are documented in
`docs/B04_GAMING_CENTERS_HANDOFF.md`.

---

## B05 — Tournament registration / PostgreSQL race protection (2026-10-11)

- Django 6.1 transactions: https://docs.djangoproject.com/en/6.1/topics/db/transactions/ — commit capacity + registration together in a short atomic transaction.
- Django 6.1 querysets: https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update — lock the parent tournament before duplicate/capacity checks.
- Django 6.1 constraints: https://docs.djangoproject.com/en/6.1/ref/models/constraints/ — use DB check/unique constraints as backstop.
- DRF session authentication: https://www.django-rest-framework.org/api-guide/authentication/ — retain SessionAuthentication and CSRF on authenticated mutation endpoints.
- DRF permissions: https://www.django-rest-framework.org/api-guide/permissions/ — public reads explicitly AllowAny with independent authentication_classes.
- PostgreSQL row locks: https://www.postgresql.org/docs/current/explicit-locking.html — serialize competitors for the final available slot.

---

## B07 — Challenges / Opponent Search (2026-10-11)

- Django transactions/row locking: https://docs.djangoproject.com/en/6.1/topics/db/transactions/ and https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update
- Django constraints/partial unique: https://docs.djangoproject.com/en/6.1/ref/models/constraints/
- PostgreSQL partial unique indexes: https://www.postgresql.org/docs/current/indexes-partial.html
- DRF SessionAuthentication/CSRF and permissions: https://www.django-rest-framework.org/api-guide/authentication/ and https://www.django-rest-framework.org/api-guide/permissions/

Decisions:
- Database enforces unordered active player pair + game uniqueness, no self-challenge and match-state consistency. Transactional writes require actor-scoped idempotency receipts.
- The published B03 game and solo-compatible format records define the offered creation choices. They do not override B08 finalized-valid-match gate.
- B07's production eligibility and synchronous match-creation services are intentionally fail-closed pending authoritative B08/B09 integration. No fake match count, rating, venue, starts_at or completed Match.
- B08's source-unique Match model requires a timezone-aware starts_at. Frozen B07 create input has no scheduling/center fields; B99 must settle truthful in-person scheduling semantics before wiring accept.
- Read-only challenge hub page uses PostgreSQL filtered counts and bounded pagination; GET never expires rows by writing.
- Financial execution added: NO.
