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

Reviewed 2026-09-06 before implementation.

### Django custom users / authentication

- Customizing authentication / custom user model: https://docs.djangoproject.com/en/6.1/topics/auth/customizing/
- Authentication in web requests, `login()` and `logout()`: https://docs.djangoproject.com/en/6.1/topics/auth/default/
- Sessions: https://docs.djangoproject.com/en/6.1/topics/http/sessions/
- CSRF protection: https://docs.djangoproject.com/en/6.1/howto/csrf/

Decisions:

- Establish `AUTH_USER_MODEL` now, before durable product migrations depend on Django's default user model. Django documents that changing the user model later is complex and requires manual schema/data work.
- Phone is the login identifier; passwords remain available only for administrative/superuser access. OTP-created player accounts receive an unusable password.
- Web authentication uses Django sessions. Login rotates/establishes the authenticated session through Django's `login()` and logout uses Django's `logout()`.
- Anonymous OTP write endpoints are explicitly CSRF-protected even though DRF API views are otherwise convenient for API clients. A bootstrap endpoint supplies a CSRF token/cookie for the same-origin TanStack web client.
- Production session and CSRF cookies remain Secure; session cookie remains HttpOnly.

### Django REST Framework

- Authentication: https://www.django-rest-framework.org/api-guide/authentication/
- Permissions: https://www.django-rest-framework.org/api-guide/permissions/
- Throttling: https://www.django-rest-framework.org/api-guide/throttling/

Decisions:

- Authenticated account endpoints use DRF `SessionAuthentication` plus `IsAuthenticated`.
- OTP/bootstrap/public-player endpoints explicitly use `AllowAny`; they do not inherit anonymous access accidentally.
- DRF throttling is not treated as the security boundary for OTP abuse. DRF itself documents that application-level throttling is not a brute-force/DDoS security control and may be fuzzy under concurrency. OTP cooldown/request-window state is therefore persisted in PostgreSQL and updated transactionally; edge/network rate limiting is an additional deployment concern.

### PostgreSQL / Django transactions

- Django transactions: https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- `select_for_update()`: https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update
- PostgreSQL explicit locking: https://www.postgresql.org/docs/current/explicit-locking.html

Decisions:

- OTP request-state and OTP verification transitions use transactions and row-level locking where concurrent mutation matters.
- Incorrect-attempt decrement, expiry consumption and successful single-use consumption are persisted before domain errors are returned; exceptions are not raised in a way that rolls those state changes back.

### Privacy / identity contract

Decision:

- `User` holds private account identity; `PlayerProfile` holds public competitive identity. Public player serialization never exposes phone, email, permissions or interview opt-in state.
- Persistent venue roles are not flattened into account booleans; venue-scoped memberships belong to the gaming-center domain in a later phase.
