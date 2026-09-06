# Official Source Audit — P00

Reviewed 2026-09-06 before implementation.

## Django 6.1

- Release notes / Python compatibility: https://docs.djangoproject.com/en/6.1/releases/6.1/
- Installation FAQ / production PostgreSQL recommendation: https://docs.djangoproject.com/en/6.1/faq/install/
- Database support and PostgreSQL notes: https://docs.djangoproject.com/en/6.1/ref/databases/
- Deployment checklist: https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/
- Settings reference: https://docs.djangoproject.com/en/6.1/ref/settings/

Decisions:

- Support Python 3.12–3.14, matching Django 6.1.
- PostgreSQL is the durable database; Django 6.1 supports PostgreSQL 15+ and recommends psycopg 3.
- Keep `CONN_MAX_AGE=0` under ASGI baseline; Django docs advise disabling persistent connections for ASGI and considering backend pooling if needed.
- Production secrets are environment-only and production config fails closed.
- CI includes Django deployment checks.

## Django REST Framework 3.18

- Release notes: https://www.django-rest-framework.org/community/release-notes/

Decision:

- Use DRF 3.18 because it explicitly adds Django 6.1 support.
- Global API policy defaults to authenticated; individual public read/health endpoints explicitly allow anonymous access.

## Celery 5.6

- Django integration: https://docs.celeryq.dev/en/stable/django/

Decision:

- Celery is the initial background-job framework. Transaction-critical truth remains synchronous; async jobs handle notifications, external IO, derived projections and other retryable work.

## Redis

- redis-py guide: https://redis.io/docs/latest/develop/clients/redis-py/
- Production usage: https://redis.io/docs/latest/develop/clients/redis-py/produsage/

Decision:

- Use redis-py through Django/queue integrations; production hardening later includes timeouts, health checks, exception handling and appropriate secure connectivity.

## PostgreSQL

- Explicit locking: https://www.postgresql.org/docs/current/explicit-locking.html

Decision:

- Race-prone domain transitions will be designed with database constraints and explicit locking only where the domain requires it; locks are not added indiscriminately.
