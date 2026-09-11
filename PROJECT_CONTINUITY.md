# TURNOMENT — BACKEND PROJECT CONTINUITY CHECKPOINT

> **MANDATORY FIRST READ FOR EVERY CHAT / AGENT / SESSION**

Last checkpoint update: `2026-09-11`

## 1. Continuation law

Every backend chat/agent MUST:
1. read this file and `PHASE_COMPLETION_PROTOCOL.md`;
2. verify exact current `main` before mutation;
3. read `docs/PHASE_REGISTRY.md` before starting/reordering a backend phase;
4. use a dedicated branch/Issue/PR;
5. never claim DONE from chat memory;
6. keep cross-repo frontend contracts explicit without pretending planned APIs are live;
7. update continuity/evidence before ending;
8. preserve exact SHA/CI/PR/Issue evidence.

## 2. Repository truth

Repository: `sajadkhavas/turnoment-backend`

Current accepted backend main / F17 docs-alignment START_SHA:

`335211d711c197a440e086bc570b86f2c5cd65f8`

P00 and P01 are terminally frozen. Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`

Cross-repo frontend contracts may be documented ahead of runtime implementation, but they do not start/reorder backend phases and MUST remain represented as:

`FRONTEND MOCK / BACKEND PENDING`

until an owning backend domain is implemented, permission-tested and merged.

## 3. Accepted cross-repo documentation alignments

F14 Teams alignment:
- backend Issue `#25` — CLOSED / COMPLETED;
- PR `#26` — MERGED;
- accepted backend main `1977db3c9995336166907b9fd85ac26093e6c254`;
- no Teams runtime Python implementation added.

F15 Challenge Hub alignment:
- backend Issue `#27` — CLOSED / COMPLETED;
- PR `#28` — MERGED;
- accepted backend main `c72ec545782a25719009ae329d74ffd13259d020`;
- post-main Backend Quality Gate `34584360023` — PASS;
- no Challenge runtime Python implementation added.

F16 Public Home Discovery alignment:
- backend Issue `#29` — CLOSED / COMPLETED;
- docs head `0338af8432d16a92ebafe85160e1d45f8ae3c8db`;
- PR `#30` — MERGED;
- accepted backend main `335211d711c197a440e086bc570b86f2c5cd65f8`;
- post-main Backend Quality Gate `34591528685` — PASS on Python 3.12 / 3.14;
- no Home discovery runtime Python implementation added.

Frontend freezes do not change backend runtime phase order.

## 4. Active cross-repo alignment — F17 Public Tournament Discovery

Frontend repository: `sajadkhavas/turnoment`.

Frontend route: `/tournaments`.

Frontend F17 START_SHA:

`fb87a7d84470db6ed1eba03ce0251c5f1eb6b7a9`

Frontend tracking Issue: `sajadkhavas/turnoment#84`.

Backend tracking Issue: `#31`.

Backend docs branch: `docs/f17-public-tournament-discovery-contract`.

Contract source: `docs/F17_PUBLIC_TOURNAMENT_DISCOVERY_CONTRACT.md`.

Status:

`IN PROGRESS — DOCUMENTATION ONLY`

The current frontend `/tournaments` inventory performs authoritative filtering/sorting/featured selection and discovery statistics over local fixture arrays. F17 replaces that browser authority with a permanent anonymous-safe tournament discovery contract while retaining validated, shareable URL navigation state.

Planned endpoint already reserved in the baseline frontend↔backend contract:

`GET /api/v1/tournaments/`

This alignment is documentation-only. Python, models, migrations, serializers, views, URLs, dependencies and `docs/PHASE_REGISTRY.md` are forbidden from changing here.

## 5. Permanent F17 tournament-discovery ownership truth

Backend/repository owns:
- accepted domain-backed game/city filter options;
- query validation at the API boundary;
- result-set membership and ordering;
- pagination totals/current page;
- tournament stable ID/slug/title;
- stable game and venue relation keys;
- venue verification/location;
- lifecycle and registration state;
- schedule/timezone;
- format/bracket labels;
- capacity limit/registered/remaining truth;
- entry fee and fixed prize money truth;
- optional curated/featured tournament identity when exposed.

Frontend may own:
- validated URL navigation state before the request;
- static Persian labels/copy and information hierarchy;
- formatting projected values;
- canonical/robots policy for faceted URL variants;
- responsive/accessibility presentation;
- deterministic fixture repository only for dev/test/visual QA.

Frontend MUST NOT authoritatively filter/sort a production inventory in the browser or infer verification, lifecycle, capacity, registration availability, fee/prize, result or ranking truth.

## 6. F17 query contract

Optional query parameters:
- `game=<stable-game-id-or-approved-slug>`;
- `city=<stable-city-value>`;
- `date=today|tomorrow|weekend|week`;
- `status=open|filling|closed|upcoming`;
- `format=1v1|team|single-elim|double-elim|round-robin`;
- `price=free|lt300|300-500|gt500`;
- `verified=true`;
- `sort=suggested|soonest|limited|cheapest|prize`;
- `page=<positive-integer>`.

Absence means the backend-defined default for that field. Frontend validation is navigation safety only; future backend implementation repeats validation independently.

## 7. F17 privacy / integrity rules

- endpoint is anonymous-safe and read-only;
- stable IDs/slugs are relation/navigation keys; display labels are presentation only;
- `registered <= limit` and `remaining = max(0, limit - registered)` whenever capacity is finite;
- venue `verified` is backend-owned;
- lifecycle and registration states must be mutually consistent;
- result ordering, pagination and optional featured identity are backend-owned;
- money uses explicit amount + currency (`IRR`);
- timestamps are offset-aware and carry `Asia/Tehran` (or another explicit IANA timezone if the owning domain later supports it);
- empty result pages are valid product states and must never trigger fabricated production fallback records;
- response exposes no phone/email, private account/profile, payment/refund/settlement, permission, moderation/dispute evidence or private Challenge data;
- Tournament Rating and Challenge Rating remain separate;
- no wager/betting/stake mechanics.

## 8. Phase boundary

F17 contract alignment does NOT add:
- Python code;
- models/migrations;
- serializers/views/URLs;
- tournaments/registrations business logic;
- gaming-center verification logic;
- dependencies;
- phase-registry changes.

The runtime tournaments/registrations owner lands only in accepted backend phase order after P02 Games/Catalog and the gaming-center/resource foundation. Until then F17 remains exactly:

`FRONTEND MOCK / BACKEND PENDING`.

## 9. Exact F17 backend alignment NEXT

1. commit exactly `PROJECT_CONTINUITY.md` and `docs/F17_PUBLIC_TOURNAMENT_DISCOVERY_CONTRACT.md` from backend START_SHA `335211d711c197a440e086bc570b86f2c5cd65f8`;
2. verify ahead 1 / behind 0 / exactly one commit / exactly two Markdown files;
3. require Backend Quality Gate PASS on Python 3.12 and 3.14;
4. open docs PR without auto-closing Issue #31;
5. require mergeable=true, unresolved review threads=0 and exact pre-merge backend `main` lock;
6. merge with expected-head lock;
7. require post-main Backend Quality Gate PASS;
8. reverify exact live backend `main`;
9. record terminal docs-alignment evidence in Issue #31 and close completed;
10. keep Backend NEXT exactly `P02 — Games / Catalog Foundation`.

Frontend F17 independently completes its implementation/SEO/QA/closeout chain. Completion of backend Issue #31 is contract alignment only and MUST NOT be described as live tournament backend implementation.
