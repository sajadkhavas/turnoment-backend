# Engineering Rules

## Mandatory phase workflow

1. Read official upstream documentation relevant to the phase.
2. Record source URLs and design implications.
3. Freeze `START_SHA`.
4. Work on a dedicated phase branch.
5. Implement smallest coherent domain slice.
6. Add positive, negative, permission and failure-path tests appropriate to the slice.
7. Run lint, Django checks, migration drift checks and test suite.
8. Run production deployment checks when settings/deployment behavior changes.
9. Review frontend contract impact.
10. Open PR; do not merge red or unreviewed work.
11. After green CI, merge and record merge SHA/END_SHA in registry.

## Data integrity

- Prefer database constraints for invariants the database can enforce.
- Multi-write business state transitions must define their transaction boundary.
- Race-prone updates must evaluate row locking and idempotency.
- A Celery task must not silently replace an atomic synchronous truth transition.
- Money uses integer minor/accounting units or a documented Decimal model; never binary float.

## API

- Version under `/api/v1/`.
- Global default permission is authenticated; public endpoints opt into `AllowAny` explicitly.
- Validation belongs in backend contracts even when frontend validates too.
- Authorization is enforced server-side, including object ownership/venue scope.
- No private user data in public player APIs.

## Security

- No credentials or production secrets in Git.
- `DEBUG=False` in production.
- Production settings fail closed when required environment variables are missing.
- HTTPS/security cookie/HSTS settings are deployment-gated.
- User uploads are untrusted and will later use validated direct/object storage paths.

## Frontend relationship

Everything mutable or business-significant visible in the frontend needs a backend owner. Pure presentation does not.

A UI screen may be designed ahead of its backend implementation, but it remains `FRONTEND MOCK / BACKEND PENDING` until the contract and domain are implemented.
