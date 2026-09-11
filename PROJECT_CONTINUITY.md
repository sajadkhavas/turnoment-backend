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

Current accepted backend main / F16 docs-alignment START_SHA:

`c72ec545782a25719009ae329d74ffd13259d020`

P00 and P01 are terminally frozen. Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`

Cross-repo frontend contracts may be documented ahead of runtime implementation, but they do not start/reorder backend phases and MUST remain represented as:

`FRONTEND MOCK / BACKEND PENDING`

until an owning backend domain is actually implemented, permission-tested and merged.

## 3. Previously accepted cross-repo documentation alignments

F14 Teams alignment:
- backend Issue `#25` — CLOSED / COMPLETED;
- PR `#26` — MERGED;
- accepted backend main `1977db3c9995336166907b9fd85ac26093e6c254`;
- no Teams runtime Python implementation added.

F15 Challenge Hub alignment:
- backend Issue `#27` — CLOSED / COMPLETED;
- docs head `184c4a5baaa5ddd464d98cd8ae01c2c65397393b`;
- PR `#28` — MERGED;
- accepted backend main `c72ec545782a25719009ae329d74ffd13259d020`;
- post-main Backend Quality Gate `34584360023` — PASS;
- no Challenge runtime Python implementation added.

Frontend F14/F15 are frozen independently. Those frontend freezes do not change backend runtime phase order.

## 4. Active cross-repo alignment — F16 Public Home Discovery

Frontend repository: `sajadkhavas/turnoment`

Frontend route: `/`

Frontend START_SHA / frozen main at F16 start:

`008f4fbd959138e3abe6bf85078f6cf700319bd2`

Backend tracking Issue: `#29`

Backend docs branch: `docs/f16-public-home-discovery-contract`

Contract source: `docs/F16_PUBLIC_HOME_DISCOVERY_CONTRACT.md`

Status:

`IN PROGRESS — DOCUMENTATION ONLY`

The existing Home frontend currently contains hardcoded discovery data for tournaments, gaming centers, ranking, aggregate stats and a featured showdown. F16 replaces that direct local authority with a permanent anonymous-safe projection contract.

Planned endpoint:

`GET /api/v1/discovery/home/`

This alignment is documentation-only. Python, models, migrations, serializers, views, URLs, dependencies and `docs/PHASE_REGISTRY.md` are forbidden from changing here.

## 5. Permanent F16 public-home ownership truth

Backend/repository owns every dynamic public discovery fact, including:
- aggregate discovery stats when exposed;
- popular/featured game identity, slug and active-tournament counts;
- allowed Home finder options that originate from product/domain data;
- featured tournament identity, lifecycle, venue, capacity, fee/prize and registration truth;
- gaming-center identity, verification, location, equipment/review projection and upcoming-tournament counts;
- ranking preview identity/rank/rating/result-derived values;
- optional featured showdown only when authoritative Match/tournament/result truth exists;
- stable IDs/slugs and typed navigation/search targets.

Frontend may own:
- static explanatory product copy;
- visual hierarchy and responsive presentation;
- temporary finder form state before navigation;
- deterministic dev/test fixture implementation behind the same repository contract.

Frontend MUST NOT infer or locally author center verification, tournament lifecycle/capacity, ranking/rating, winner/result, aggregate stats or other backend-owned truth.

## 6. F16 privacy / integrity rules

- `GET /api/v1/discovery/home/` is anonymous-safe and read-only.
- It must not expose private account, phone, email, permission, payment or moderation data.
- Stable identifiers are relation/navigation keys; display names are presentation only.
- Empty arrays and an absent optional showdown are valid states.
- Production frontend must not fall back to fabricated fixture truth when the endpoint is unavailable.
- Tournament Rating and Challenge Rating remain separate.
- no wager/betting/stake mechanics.
- the Home projection does not change the authority of owning domains; it is an aggregation/projection surface only.

## 7. Official-source decisions retained for F16

Frontend independently audits current TanStack Start/Router, Google Search Central and WCAG guidance.

Backend alignment decisions:
- endpoint is safe GET only and side-effect free;
- anonymous response is explicitly public-safe;
- future domain implementation must source each field from the owning domain rather than duplicate business truth in a Home-specific model;
- no runtime implementation is authorized before owning backend phases exist in accepted order.

## 8. Exact F16 backend alignment NEXT

1. keep this alignment diff documentation-only;
2. require exact compare from `c72ec545782a25719009ae329d74ffd13259d020`;
3. require Backend Quality Gate PASS on Python 3.12 and 3.14;
4. open docs PR without auto-closing Issue #29;
5. require mergeable=true, unresolved review threads=0 and exact pre-merge backend `main` lock;
6. merge with expected-head lock;
7. require post-main Backend Quality Gate PASS;
8. reverify exact live backend `main`;
9. record terminal docs-alignment evidence in Issue #29 and close completed;
10. keep Backend NEXT exactly `P02 — Games / Catalog Foundation`.

Frontend F16 independently completes its implementation/SEO/QA/closeout chain. Completion of backend Issue #29 is contract alignment only and MUST NOT be described as live Home backend implementation.
