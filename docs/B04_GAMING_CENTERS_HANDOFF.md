# B04 — Gaming Centers / Host / Resources implementation handoff

Issue #50. Dedicated branch: phase/b04-gaming-centers-host-resources.
Execution START_SHA: 0f5d44646b608106ad20db97ec8c559fa084e6ce.
Frozen frontend contract: sajadkhavas/turnoment @ 1668109bae5ec7abb5e022e5857ffa65cc131501.

## API ownership
- Anonymous GET /api/v1/centers/ (stable city/page projections).
- Anonymous GET /api/v1/centers/{publicId}/ (public, publication-gated).
- Anonymous POST /api/v1/host-applications/ (public form, 201 receipt, 400 validation, 429 quota).
- Center-scoped GET/PATCH /api/v1/center-admin/centers/{uuid}/.
- Center-scoped GET/POST staff, GET/POST equipment, GET/POST stations, GET/PUT hours.
- Membership role changes require an active center owner. No center API can assign owner or platform admin role.

## Data / trust rules
- Public projection omits all account contacts, staff, moderation, unpublished media, and host PII.
- Business phone/address/map are independently opted into via show_phone/show_address/show_map.
- Publication and verification are platform-curated via Django admin; ordinary center roles cannot edit these fields.
- Anonymous submission deliberately uses authentication_classes=[] + AllowAny to match session-independent F23.
- Persistent PostgreSQL rate bucket is keyed by HMAC(SECRET_KEY, REMOTE_ADDR) and locks with select_for_update.
- Five accepted unique applications per source IP per UTC hour; duplicate canonical payload within 15 minutes
  returns the same receipt without incrementing quota. Source IP headers cannot override REMOTE_ADDR.
- Raw source IP is not persisted; submission PII is accessible only to platform moderation/admin.
- Retention policy: 180 days, with B10 responsible for scheduling the purge and documenting legal exceptions.
- No public host application read/list routes are exposed. All future approval workflows belong to B10.
- Gallery bounded by position 0..7, opening hours unique by center/day, station codes and staff unique per center.
- Station/equipment same-center invariant is checked by model clean and write API; any alternate ingestion
  path must call full_clean or the scoped service (relational cross-row check cannot be a CHECK constraint).

## Integration seams
- B05 is owner of upcoming tournament count and tournament list. Until linked, count is null, list is empty;
  the backend never claims an authoritative zero or fabricates a tournament.
- B10 owns moderation/approval and timed PII deletion. Owner membership must be assigned during platform
  approval via a trusted service/admin, never via public host receipt or center-staff creation.
- B01/B99 own normalization of config/settings/base.py and config/urls.py common registrations.
- No client balance, payment URL, settlement, payout, stake, or financial transition.

## Official documentation checked
- https://docs.djangoproject.com/en/6.1/ref/models/constraints/
- https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update
- https://www.django-rest-framework.org/api-guide/permissions/
- https://www.django-rest-framework.org/api-guide/authentication/
- https://www.django-rest-framework.org/api-guide/throttling/

For terminal acceptance use exact GitHub Actions run evidence; do not describe CI as passed until both Python
3.12 and 3.14 steps complete green. FINANCIAL EXECUTION ADDED: NO.
