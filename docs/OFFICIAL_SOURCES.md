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

## B06 — Teams / Membership / Nonfinancial Achievements (2026-10-11)

- Django 6.1 constraints: https://docs.djangoproject.com/en/6.1/ref/models/constraints/ — partial unique constraints prevent duplicate member rows, simultaneous captains and outstanding duplicate invitations; a per-team captain's existence remains a transactional service invariant.
- Django 6.1 transactions: https://docs.djangoproject.com/en/6.1/topics/db/transactions/ — membership plus invitation transitions are atomic, including captain swap and increment/event persistence.
- Django 6.1 query locking: https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update — lock the parent team or user consistently to serialize concurrent competing writes.
- PostgreSQL explicit locking: https://www.postgresql.org/docs/current/explicit-locking.html — row locks serialize acceptance/transfer and replay without unsafe in-memory locks.
- DRF session authentication: https://www.django-rest-framework.org/api-guide/authentication/ — inherit P01 SessionAuthentication; no anonymous mutation override or token-auth bypass.
- DRF permissions: https://www.django-rest-framework.org/api-guide/permissions/ — private team/achievement API uses IsAuthenticated; captain and invite-recipient permissions enforced in domain services, never through client role claims.
- DRF serializers: https://www.django-rest-framework.org/api-guide/serializers/ — validate create/invite/transfer inputs, strict fields and UUIDs at boundary.

Decision: private F14/F13 projections exactly follow frontend SHA
`1668109bae5ec7abb5e022e5857ffa65cc131501`.
No public roster, participant finance, gamified currency or achievements self-claim surface.
B05 eligibility is an opt-in read-only seam; actual team registration rules remain integration-owned.

---

## B08 — Matches / Results / Disputes (2026-10-11)

Authoritative implementation references:
- Django 6.1 transaction and transaction.atomic: https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- QuerySet.select_for_update: https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update
- Unique and check constraints: https://docs.djangoproject.com/en/6.1/ref/models/constraints/
- DRF authentication/CSRF: https://www.django-rest-framework.org/api-guide/authentication/
- DRF parsers and file upload handling: https://www.django-rest-framework.org/api-guide/parsers/
- PostgreSQL transaction row locks: https://www.postgresql.org/docs/current/explicit-locking.html

Decisions:
- Each authoritative source (tournament or challenge ID) has exactly one Match. Idempotent repeat can return the original only when participants, game, competition, scheduled start and provided snapshots match; conflicting replay fails closed.
- Result confirmation/finalization locks the Match row, checks real opponent identity and creates one durable FinalizedResultEvent. B09 consumes it with a separate exactly-once receipt; neither consumer nor Celery decides primary match truth.
- Evidence upload is private quarantined binary data without public URL; signature and 5MiB limits are not malware scanning. Admin review and private evidence delivery require an explicitly approved secure operational pipeline.
- Match lifecycle has required starts_at in the frozen frontend F05 result contract; F15 challenge creation contains no venue/date/time, so B07 acceptance cannot truthfully schedule its Match until B99 defines the policy. Never substitute a fabricated clock time.
- Only authenticated participants see private result/dispute/evidence metadata. Center staff must not inherit central dispute resolution authority.
- Financial execution added: NO.

---

## B09 — Rankings / Stats / Rivalries (2026-10-11)

Official references:
- Django 6.1 transactions: https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- Django 6.1 row locking: https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update
- Django model constraints: https://docs.djangoproject.com/en/6.1/ref/models/constraints/
- Django QuerySet count/slicing: https://docs.djangoproject.com/en/6.1/ref/models/querysets/
- PostgreSQL locking: https://www.postgresql.org/docs/current/explicit-locking.html
- DRF permissions: https://www.django-rest-framework.org/api-guide/permissions/

Decisions:
- B08 FinalizedResultEvent is the sole rating source; receipt uniqueness on event+match forbids duplicate Elo changes and conflicting replay. B09 does not generate, adjust or cancel match truth.
- A trusted consumer locks season before rating row updates. Backfill of past events must be chronological; missing/multiple seasons fail closed; no invented initial season.
- Tournament and challenge Elo are independent. Ranking page counts and slices on PostgreSQL rather than materializing full leaderboards. Duplicate/unknown query filters fail closed.
- Public username publication is separate from P01 gamer_tag. B02/B09 public-profile route ownership must be explicitly reconciled at B99; no identity fields are exposed by default.
- B08 is unmerged, and exact real B08→B09 integration tests and consumer scheduling are acceptance blockers for B09 to be marked DONE. B06 team matches and prior ranking movement snapshots remain deliberately deferred.
- Financial execution added: NO.

---

## B10 — Notifications / Moderation / Platform Admin (2026-10-11)

Authoritative references:
- Django 6.1 transaction.atomic: https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- Django select_for_update: https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update
- Django model constraints: https://docs.djangoproject.com/en/6.1/ref/models/constraints/
- Django custom AdminSite and AdminConfig: https://docs.djangoproject.com/en/6.1/ref/contrib/admin/#customizing-the-adminsite-class
- DRF SessionAuthentication and CSRF: https://www.django-rest-framework.org/api-guide/authentication/
- DRF permissions: https://www.django-rest-framework.org/api-guide/permissions/
- DRF serializer validation: https://www.django-rest-framework.org/api-guide/serializers/

Decisions:
- Published notifications only reflect persisted authoritative domain facts. An exact recipient+event_key receipt ensures idempotent delivery, and no client-controlled notification write endpoint exists. Mark read actions lock user and notification, retain first read timestamp and stay CSRF protected.
- Typed navigation targets cannot represent untrusted external URLs; public responses exclude users' sensitive contact, OTP and session details.
- Platform operator requires is_active AND is_staff AND is_superuser; center ownership/staff cannot imply central administrative privileges. Django Admin is protected by custom AdminSite.
- Moderation case and audit decisions do not directly change B04 host application or B08 disputed match truth. B99 must wire domain-owned transitions with audited authorization, 180-day host application PII purge policy and private evidence scanning/delivery.
- Duplicate and unknown API query params are rejected, not ambiguously interpreted.
- Financial execution added: NO.

---

## B02 — Accounts / Player / Settings

Reviewed 2026-10-11 against frontend contract `1668109bae5ec7abb5e022e5857ffa65cc131501`; implementation branch `phase/b02-accounts-player-settings`.

- Django 6.1 transactions: https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- Django 6.1 queryset row locking: https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update
- Django CSRF: https://docs.djangoproject.com/en/6.1/howto/csrf/
- Django custom user authentication: https://docs.djangoproject.com/en/6.1/topics/auth/customizing/
- DRF authentication: https://www.django-rest-framework.org/api-guide/authentication/
- DRF permissions: https://www.django-rest-framework.org/api-guide/permissions/
- DRF serializer validation: https://www.django-rest-framework.org/api-guide/serializers/

Decisions:
- Preserve the P01 session/OTP authentication boundary. Notification settings writes require a real authenticated session plus CSRF.
- Per-user preferences are versioned with an opaque revision; use a database row lock for concurrent updates and return a typed stale result instead of last-write-wins.
- Required account/system categories are never mutable. B09 owns explicit opt-in publication and public-player competitive profiles. B02 must not create an alternative gamer-tag-only public profile or expose private bio.
- B02 role checks delegate platform operator authority to B10's is_active+is_staff+is_superuser restriction and use B04's real owner/manager/staff center membership roles.
- Global platform-operator authority is distinct from object-scoped center membership; B04 owns the durable membership model.
- Dashboard and competitive results must be composed from B05/B07/B08/B09/B10 authoritative sources during B99 integration, not from placeholders.
- No financial execution.

---

## B07 — Challenges / Opponent Search (2026-10-11)

- Django transactions/row locking: https://docs.djangoproject.com/en/6.1/topics/db/transactions/ and https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update
- Django constraints/partial unique: https://docs.djangoproject.com/en/6.1/ref/models/constraints/
- PostgreSQL partial unique indexes: https://www.postgresql.org/docs/current/indexes-partial.html
- DRF SessionAuthentication/CSRF and permissions: https://www.django-rest-framework.org/api-guide/authentication/ and https://www.django-rest-framework.org/api-guide/permissions/

Decisions:
- Database enforces unordered active player pair + game uniqueness, no self-challenge and match-state consistency. Transactional writes require actor-scoped idempotency receipts.
- The published B03 game and solo-compatible format records define the offered creation choices. They do not override B08 finalized-valid-match gate.
- B07 now counts only completed persisted B08 FinalizedResultEvent records and reads B09 Challenge Rating only if a single unambiguous published scope exists. Creation stays disabled until truthful schedule/venue semantics and real synchronous B08 Match binding are approved. No fake match, rating or starts_at.
- B08's source-unique Match model requires a timezone-aware starts_at. Frozen B07 create input has no scheduling/center fields; B99 must settle truthful in-person scheduling semantics before wiring accept.
- Read-only challenge hub page uses PostgreSQL filtered counts and bounded pagination; GET never expires rows by writing.
- Financial execution added: NO.


---

## B02/B99 owner dashboard integration — 2026-10-12

Frontend authority: `sajadkhavas/turnoment@1668109bae5ec7abb5e022e5857ffa65cc131501`.
Backend reviewed baseline: `347782fc7b961b9a63f316994cb5269d982adda3`.

- Django transactions and ORM aggregation: https://docs.djangoproject.com/en/6.1/topics/db/transactions/ and https://docs.djangoproject.com/en/6.1/topics/db/aggregation/
- Django QuerySet lookups: https://docs.djangoproject.com/en/6.1/ref/models/querysets/
- DRF authentication and object-level permissions: https://www.django-rest-framework.org/api-guide/authentication/ and https://www.django-rest-framework.org/api-guide/permissions/
- OWASP API security (object access): https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/

Decisions:
- `GET /api/v1/me/dashboard/` is session-authenticated and owner-only; accepts no arbitrary filters.
- B08 finalized-result records, B09 applied rating receipts, B05 confirmed registrations, B07 challenges, B06 teams/achievements and B10 notifications are read as durable truth.
- Absent rating scope, published rank, or public username is explicitly `null`, never an invented positive rank/score/public profile.
- The frozen frontend's `tournamentRank: positiveInt` and unconditional public-profile link are demonstrable empty-account contract bugs; a dedicated B99 frontend compatibility branch handles `null` without modifying historical contract SHA.
- No payment, wallet, settlement, wager or prize payout.
