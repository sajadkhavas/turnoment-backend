# Architecture — P00

## Shape

Turnoment uses two repositories with an explicit contract boundary:

```text
TanStack Start / React / SSR
        |
        | HTTPS / versioned API
        v
Django + Django REST Framework
        |
        +-- PostgreSQL: durable business truth
        +-- Redis: cache / ephemeral coordination / Celery broker
        +-- Celery: background jobs
        +-- Object storage: media later
```

The backend begins as a **modular monolith**. Microservices are not introduced without a measured scaling or isolation requirement.

## Authority boundary

Backend-authoritative:

- users, identities and permissions
- games and game policies
- gaming centers and resources
- tournament templates, tournaments, registration, check-in
- brackets, rounds, matches, results, evidence and disputes
- rankings and rating events
- challenges and rivalries
- stories/content metadata that admins can manage
- notifications state
- payments, refunds, ledger, prizes and settlements
- moderation, audit and analytics facts
- SEO fields attached to backend entities

Frontend-owned:

- component composition
- spacing, typography implementation and animation
- local optimistic presentation that never becomes durable truth
- accessibility/presentation behavior

## Domain roadmap

Planned Django apps/modules:

`accounts`, `players`, `games`, `gaming_centers`, `gaming_resources`, `seasons`, `tournaments`, `registrations`, `checkins`, `teams`, `clans`, `brackets`, `matches`, `results`, `disputes`, `rankings`, `challenges`, `rivalries`, `stories`, `media`, `follows`, `notifications`, `achievements`, `reviews`, `payments`, `ledger`, `settlements`, `moderation`, `audit`, `analytics`, and later `reservations` / `agents`.

These names describe bounded modules, not separate network services.

## Transaction rule

Critical state transitions are synchronous database operations. When a future operation can race (capacity reservation, final result, payment/refund, ranking event, settlement, resource reservation), implementation must consider database constraints, `transaction.atomic()`, row locks such as `select_for_update()`, idempotency and audit evidence.

Background jobs must not become the source of truth for a transaction that must commit atomically.

## Async rule

Do not convert business logic to async merely because ASGI exists. Async is reserved for workloads that benefit from it. Transaction-heavy Django logic remains synchronous until Django provides a safe transactional async path and the phase has evidence supporting its use.

## API versioning

Public contract prefix: `/api/v1/`.

Breaking contract changes require either a backward-compatible migration window or a new API version. Frontend mocks should converge toward the documented API shape instead of becoming a second domain model.
