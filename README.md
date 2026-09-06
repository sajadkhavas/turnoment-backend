# Turnoment Backend

Production backend and domain source of truth for the Turnoment competitive gaming platform.

## P00 baseline

- Frontend repository: `sajadkhavas/turnoment`
- Frontend baseline SHA: `8d5736d788235e3e99765a5332f79f0cba861482`
- Backend bootstrap SHA: `16540a37809c0c4e06a1cd5f6ee03bd88002fdc4`
- Phase branch: `phase/p00-backend-foundation`
- API prefix: `/api/v1/`

## Stack

- Python 3.12–3.14
- Django 6.1
- Django REST Framework 3.18
- PostgreSQL 15+ (local/CI baseline: PostgreSQL 17)
- Redis
- Celery 5.6

The architecture is a modular monolith. Business rules live in Django; the TanStack Start frontend is a client of versioned backend contracts. AI/agent workloads may be added later, but agents must call the same permission-checked service layer as human-facing APIs.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e '.[dev]'
cp .env.example .env

docker compose up -d postgres redis
export DJANGO_SETTINGS_MODULE=config.settings.local
python manage.py migrate
python manage.py runserver
```

Health endpoints:

- `GET /health/live/`
- `GET /health/ready/`
- `GET /api/v1/system/meta/`

## Quality gate

```bash
ruff check .
python -m compileall -q apps config manage.py
python manage.py check --settings=config.settings.test
python manage.py makemigrations --check --dry-run --settings=config.settings.test
pytest -q
```

Production deploys must also pass Django's deployment checks against `config.settings.production`.

## Rules

1. No secrets in Git. Production secrets come only from environment/secret storage.
2. No direct feature work on `main`; use a phase branch and PR.
3. Frontend business data and mutable content must have a backend owner/API contract.
4. UI-only concerns (spacing, animation, local component presentation) remain frontend-owned.
5. Financial, tournament, ranking, result, permission and inventory/resource truth is backend-authoritative.
6. Sensitive writes must eventually use transactions, constraints, locks, idempotency and audit evidence where applicable.
7. Official upstream documentation is reviewed before each implementation phase.

See `docs/` for architecture, contracts, engineering rules, registry and official-source audit.