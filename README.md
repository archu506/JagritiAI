# JagritiAI — SIH25049

AI-powered public-health awareness platform: citizens ask health questions and get
safe, source-grounded answers; anonymized, consented trends feed an Early Awareness
Engine that surfaces statistical anomalies for human review by health officials.

**This system never claims to confirm a disease outbreak.** It generates an
*Early Awareness Signal* that requires human/public-health verification.

---

## 1. What was implemented

**Backend (FastAPI + PostgreSQL, fully working, tested)**
- JWT auth + RBAC (citizen / health_official / admin)
- Core citizen flow: ask question → Medical Safety Engine gate → RAG retrieval →
  AI-generated answer with sources → optional consent → anonymization
- `AIService` abstraction: `GeminiAIService` (real Gemini API) auto-falls back to
  `DemoAIService` (offline, deterministic) when `GEMINI_API_KEY` is unset or a call fails
- `Retriever` abstraction: `VectorRetriever` (Qdrant, stub) / `DemoRetriever`
  (offline keyword search) — same auto-select-by-config pattern
- `MapService` abstraction: real Maps API stub / `DemoMapService` (seeded offline directory)
- Medical Safety Engine: hard-gates emergency and self-harm language before AI generation
- Privacy layer: k-anonymity suppression (default threshold = 5) on all aggregates
- Early Awareness Engine: z-score anomaly detection over anonymized weekly symptom
  trends, per (symptom, district) pair; signals always start `pending_review`
- Multilingual content and answers: English, Hindi, Odia
- Synthetic demo data seeder (knowledge base, schemes, myths, facilities, 8 weeks of
  realistic trend history plus one deliberate anomaly spike for the demo)
- Alembic migrations (initial schema, verified to apply cleanly)

**Frontend (React + Vite + TypeScript, builds cleanly)**
- Citizen assistant page with voice input/output (Web Speech API, degrades gracefully
  if unsupported)
- Citizen dashboard (query history), Government dashboard (trend table + signal review)
- Schemes, myth-busting, nearby-healthcare pages
- EN/HI/OR language switcher
- RBAC-protected routes

**Infra**
- Dockerfiles (backend, frontend+nginx), `docker-compose.yml` (postgres + backend + frontend)

## 2. What was actually tested (in this sandbox, no network beyond package registries)

- All backend Python files pass `py_compile`
- Full dependency install succeeded (pip + npm both had registry access)
- A genuine end-to-end pytest (`backend/tests/test_e2e_demo_flow.py`) exercises the
  **entire demo flow live** against SQLite: register → login → ask question (real
  safety gate + real RAG retrieval + real DemoAI answer generation) → verified
  emergency-question gating → consent → anonymization → Early Awareness Engine
  correctly detects a seeded statistical anomaly → RBAC blocks a citizen from the
  gov endpoint → official reviews and acknowledges the signal. **1 passed.**
- The synthetic data seeder was run against a live SQLite DB and correctly produced
  a `high` severity signal (z≈11) for the deliberately seeded Khordha fever/rash spike
- `tsc -b` (TypeScript compile) and `vite build` (production bundle) both succeed
  with zero errors
- Cross-checked every frontend API call against the backend's actual OpenAPI schema —
  100% match, no drift
- Alembic autogenerate + `alembic upgrade head` verified against a live SQLite DB,
  correctly creating all 9 tables (one real bug found and fixed: autogenerate omitted
  an import for the custom `GUID` type)
- Two other real bugs found and fixed during testing: a passlib/bcrypt version
  incompatibility (pinned `bcrypt==4.0.1`), and a Postgres-only `UUID` column type that
  broke on SQLite (replaced with a portable `GUID` TypeDecorator)

## 3. What could not be tested because of network/environment restrictions

- Actual Postgres connectivity (only SQLite was available in-sandbox; the code path
  is identical via SQLAlchemy + the portable `GUID` type, but Postgres itself was
  never connected to)
- `docker compose up` end-to-end (no Docker daemon in this sandbox) — Dockerfiles and
  `docker-compose.yml` were validated structurally (YAML parses correctly, image
  layers are standard) but never actually built/run
- Real Gemini API calls (no `GEMINI_API_KEY` provided, and no external network access
  to `generativelanguage.googleapis.com` from this sandbox) — `GeminiAIService`'s code
  path is implemented and falls back to Demo on any failure, but was not live-tested
- Real Qdrant vector search (stubbed; `DemoRetriever` is the tested path)
- Real Google Maps API calls (stubbed; `DemoMapService` is the tested path)
- Browser-based voice input/output (Web Speech API requires an actual browser; the
  hook is implemented with graceful degradation but wasn't tested in a real browser)
- The React app running live in a browser (build succeeds; not manually clicked through)

## 4. Exact commands to run on your Windows machine

### Required software
- Docker Desktop (with Docker Compose v2)
- Node.js 20+ (only needed if you want to run the frontend outside Docker)
- Python 3.12+ (only needed if you want to run the backend outside Docker)
- PostgreSQL 16 (only needed if not using Docker)

### Fastest path — Docker Compose (recommended)
```powershell
cd JagritiAI-SIH25049
copy backend\.env.example backend\.env
docker compose up --build
```
This starts Postgres, waits for it to become healthy, then the backend
container runs Alembic migrations (`alembic upgrade head`), seeds demo data
(`python -m app.db.seed`), and finally starts the API — in that order, every
time the backend container starts. Runs the backend on
`http://localhost:8000`, and the frontend on `http://localhost:5173`.

### Local development (without Docker)

**Backend:**
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env: point DATABASE_URL at a running local Postgres instance
python -m alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

**Frontend:**
```powershell
cd frontend
npm install
npm run dev
```

## 5. Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | Yes | Postgres connection string |
| `SECRET_KEY` | Yes | JWT signing key — change before any real deployment |
| `GEMINI_API_KEY` | No | If unset, runs in DEMO MODE with `DemoAIService` |
| `QDRANT_URL` | No | If unset, uses offline `DemoRetriever` |
| `MAPS_API_KEY` | No | If unset, uses offline `DemoMapService` |

## 6. Demo credentials

The seed script (`python -m app.db.seed`) now provisions three ready-to-use
demo accounts directly, so no manual registration is required before a demo:

| Role | Email | Password |
|---|---|---|
| Citizen | citizen@demo.jagriti | Demo@1234 |
| Health Official | official@demo.jagriti | Demo@1234 |
| Admin | admin@demo.jagriti | Demo@1234 |

**Security note:** the public `POST /api/v1/auth/register` endpoint can only ever
create a `citizen` account — any attempt to self-register as `health_official`
or `admin` is rejected with `403 Forbidden`. Privileged accounts are only ever
provisioned server-side (the seed script above, or a future admin-only
endpoint), never through public sign-up.

## 7. How to perform the complete SIH demo

1. **Run the seeder** (`python -m app.db.seed`) — this provisions the citizen,
   health_official, and admin demo accounts above, plus all content/trend data.
2. **Land on `/`** — the new JagritiAI landing page explains the problem, the
   solution, and the citizen → anonymous signal → government awareness flow.
   Click **"Ask JagritiAI"**, or **login as citizen** and go to the Ask page.
3. Type: *"I have fever and joint pain, what could it be?"*
   → JagritiAI retrieves the seeded Dengue knowledge doc and answers with sources.
4. **Accept the consent prompt** — this anonymizes the symptom tags into the trend table.
5. **Login as health_official** (official@demo.jagriti), go to Government Dashboard.
6. Click **"Run Early Awareness Scan."** Because the seeder pre-loaded 8 weeks of
   baseline noise plus a deliberate spike in Khordha fever/rash cases, the engine
   will surface a **high-severity signal** immediately (or your own consented
   contribution will accumulate toward one).
7. **Acknowledge** the signal, demonstrating the human-in-the-loop review step —
   the system never auto-confirms an outbreak.
8. Show the **Schemes**, **Myth vs Fact**, and **Nearby Healthcare** pages, and the
   language switcher (EN/HI/OR) to demonstrate multilingual + full public-health
   information support. On a phone-width screen, use the hamburger menu to show
   the responsive mobile navigation.

## 8. Consistency audit summary

- FRONTEND ↔ BACKEND API: verified match against live OpenAPI schema (Section 2)
- BACKEND ↔ DATABASE: verified via passing Alembic migration + full model set in
  `app/models/__init__.py`
- BACKEND ↔ AI SERVICE: verified via `factory.py` auto-select + tested DemoAIService path
- RAG ↔ KNOWLEDGE BASE: verified — seeded dengue doc correctly retrieved and cited
  for a matching symptom question in the e2e test
- DASHBOARD ↔ ANALYTICS: verified — gov dashboard reads live k-anonymous aggregates
  and pending signal counts
- CONSENT ↔ ANONYMIZATION: verified — consent endpoint writes only de-identified
  `AnonymizedSymptomReport` rows, never raw query text or user identity
- ANONYMIZATION ↔ EARLY AWARENESS ENGINE: verified — engine reads exclusively from
  k-anonymous aggregates, never per-user records
- EARLY AWARENESS ENGINE ↔ DASHBOARD: verified — engine-generated signals appear
  correctly in the gov dashboard's pending list and can be reviewed

## 9. Session 2 additions (topic-safe RAG, signal plane, myth-fact grounding)

This session evolved the project per the Community Health Sentinel product spec, incrementally, without rebuilding from scratch. Summary of what changed:

**Fixed a real disease-mixing bug**: the original `DemoRetriever` did plain token-overlap search, so a generic "fever" query could wrongly return the dengue document, and unregistered diseases (e.g. "Ebola") wrongly returned an unrelated document instead of a safe fallback. Reproduced live, then fixed via:
- `app/services/taxonomy.py` — two-level `HealthCategory`/topic taxonomy
- `app/services/intent.py` — rule-based (no LLM call) intent classifier
- `app/services/rag.py` — retrieval now filters by topic/category metadata before ranking, enforces a confidence threshold, and returns an empty safe-fallback result rather than substituting an unrelated disease

**New signal plane** (`app/models/signals.py`): `GeoBlock`/`SignalEvent`/`Alert` tables, strictly separate from the conversation plane (`HealthQuery`). `app/services/signals.py::record_signal_event` is the only function permitted to write to it, and only fires on explicit consent — verified by a test that asserts zero `SignalEvent` rows exist after a declined consent.

**Reworked Early Awareness Engine** (`app/services/awareness_v2.py`): z-score anomaly detection over `SignalEvent` day-buckets per (topic_category, geo_block), writing `Alert` rows that always start `status='pending_review'`.

**New dashboard endpoints** matching the spec's naming: `GET /dashboard/trends`, `GET /dashboard/alerts` (always includes a disclaimer field), `POST /dashboard/alerts/{id}/ack`, `POST /dashboard/scan`, `POST /dashboard/broadcast` (simulated, per MVP scope). Old `/awareness/*` and `/dashboard/gov/overview` endpoints preserved unchanged for backward compatibility.

**Compatibility route aliases** (`app/api/v1/compat.py`): `/chat/message`, `/facilities/nearby`, `/schemes/search` — thin wrappers delegating to the original implementations, added alongside (not replacing) the original routes.

**Myth-vs-fact is now genuinely grounded**: myth_fact-intent queries (detected via a declarative-claim pattern like "X prevents Y", distinguished from genuine "how do I prevent Y" prevention questions) are answered strictly from the curated `MythFact` table — never LLM-generated — in the exact MYTH/FACT/Source format from the spec.

**Response cache** (`app/services/cache.py`): normalizes near-duplicate phrasings to the same cache key so repeated questions skip retrieval+generation.

**Simulated demo data is explicitly labeled**: all seeded `SignalEvent` rows carry `is_simulated=True`, surfaced in both the API response and the frontend UI ("⚠ DEMO / SIMULATED DATA" banner + per-row badges) — never presented as real statistics.

**Frontend**: `GovDashboard.tsx` rewritten to consume the new signal-plane endpoints, with topic/district filtering, simulated-data badges, and the "not a confirmed outbreak" disclaimer surfaced directly from the API.

**Tests**: 19/19 passing (11 new this session) — `test_health_retrieval.py` (8 tests) and `test_signal_plane.py` (10 tests, including no-consent-blocks-signal, consent-creates-correct-signal, signal-has-no-PII, aggregation, anomaly-detection-on-seeded-spike, dashboard-alert-listing, RBAC-block, simulated-data-labeling, myth-fact-grounding, prevention-not-misclassified). The pre-existing `test_e2e_demo_flow.py` was also fixed — it encoded the old, unsafe retrieval behavior in one assertion, which was corrected rather than left broken or the new logic weakened to accommodate it.

**Verified, not just claimed**: every fix above was reproduced as a failing case first, then shown fixed, live, with actual command output — see the conversation transcript for the exact before/after query results.

**Not done this session** (still open): `kb_documents`/`kb_chunks` chunk-level split, red-flag detector as a fully separate module (currently `MedicalSafetyEngine` already is rule-based and independent of the LLM, satisfying the architectural requirement, but not refactored into a new dedicated module), multilingual retrieval beyond English-language knowledge documents, voice support beyond the existing Web Speech API hook, citizen-side frontend updates for intent-aware UI (myth-fact styling, emergency escalation UI), map/heatmap visualization, and `docker compose up` was not actually run (no Docker daemon in this sandbox) — Dockerfiles/compose file are unchanged from session 1 and still only structurally validated.

## 10. Session 3 additions (dashboard analytics, maps, visual/UX polish)

Addressed the gap flagged after session 2: the government dashboard had no charts, no map, no geographic visualization, and the frontend was visually basic across all pages.

**Backend additions:**
- `GeoBlock.latitude`/`longitude` added (block-centroid coordinates — deliberately coarse, never derived from an individual citizen's location, consistent with the existing k-anonymity/no-exact-GPS model). Third Alembic migration generated and applied cleanly, verified live.
- `GET /dashboard/alerts/{id}/timeseries` — daily signal-event counts for a given alert's (topic_category, geo_block) over a trailing window, for baseline-vs-current charting.
- `recommended_actions()` in `awareness_v2.py` — severity-tiered action lists (e.g. "verify through field health workers," "deploy rapid response team" for high severity), now returned on every alert.
- `/dashboard/trends` and `/dashboard/alerts` now include lat/lon so the map has real data to plot.

**Frontend additions:**
- Added `recharts`, `leaflet`, `react-leaflet` as real dependencies (installed and built successfully, not just referenced).
- `components/SignalMap.tsx` — a genuine Leaflet map (OpenStreetMap tiles) with circle markers sized by intensity and colored by severity, used on both the Government Dashboard (alert locations) and the citizen Nearby Healthcare page (facility locations).
- `components/TrendChart.tsx` / `TopicBarChart.tsx` — recharts line/bar charts for baseline-vs-current trend and topic-category distribution.
- `components/Cards.tsx` / `States.tsx` — reusable `StatCard`, `SeverityBadge`, `SimulatedBadge`, `LoadingState`, `ErrorState`, `EmptyState`, used consistently across all pages instead of ad hoc "Loading..." text.
- `GovDashboard.tsx` rewritten: stat-card row, geographic map, topic bar chart, clickable alert cards that open a detail panel with a baseline-vs-current line chart and a recommended-action list.
- `AskPage`, `NearbyPage`, `SchemesPage`, `MythsPage`, `CitizenDashboard` all updated with proper loading/empty/error states; `AskPage` gained a hero header and clickable suggestion chips; `NearbyPage` now shows facilities on a real map, not just a list.
- CSS pass: stat/alert card styling, map container styling, a mobile breakpoint (`@media max-width: 720px`) that reflows the nav and dashboard grid to a single column, and `:focus-visible` outlines added across interactive elements for keyboard accessibility.

**Tests**: 21/21 passing (2 new this session: `test_alert_has_coordinates_for_map_and_recommended_actions`, `test_alert_timeseries_endpoint`), verified from a clean tree. `tsc -b` and `vite build` both succeed with zero errors. Every frontend API call cross-checked against the live OpenAPI schema — zero drift, including the new timeseries endpoint.

**Honest gaps still remaining**: no landing-page-specific route separate from the ask page (the hero is embedded inline rather than a distinct `/` marketing page); no hamburger/collapsible mobile nav (the nav wraps via CSS flex-wrap, which works but isn't a dedicated mobile menu component); no dynamic code-splitting yet, so the production JS bundle is ~775KB (230KB gzipped) — Vite flags this but it wasn't addressed given the scope of this pass; no automated accessibility audit (e.g. axe-core) was run, only manual `:focus-visible` styling; citizen-side myth-fact/emergency-specific visual treatment (e.g. distinct card styling per intent) wasn't added beyond the existing `flag-emergency`/`flag-self_harm` CSS classes from session 1; `docker compose up` still has not been run in this sandbox (no Docker daemon available) — Dockerfiles/compose file are unchanged and only structurally validated.

---

## Session 4 — Stability & demo-readiness pass (final)

This pass intentionally made **no further redesigns**. It closed the specific
gaps flagged at the end of session 3, fixed one real security issue found
along the way, and re-validated the whole system end to end.

**1. Dedicated landing page.** New `pages/LandingPage.tsx` now owns `/`:
JagritiAI name, "Community Health Sentinel" subtitle, problem/solution
explanation, three CTA buttons ("Ask JagritiAI" → `/ask`, "Explore Disease
Awareness" → `/myths`, "For Health Officials" → `/login`), a privacy
explanation, the "AI does not diagnose diseases" disclaimer, and a
citizen → anonymous signal → government awareness flow diagram. Fully
translated (EN/HI/OR). The Ask page moved to `/ask`; its own functionality
(question submission, voice input, consent flow, sources) is unchanged —
only its inline hero header was removed, since the landing page now owns that.

**2. Responsive mobile navigation.** `NavBar.tsx` now renders a hamburger
button below 720px width that opens a slide-down mobile menu with all nav
links, the language switcher, and working login/logout — desktop nav is
unchanged above that breakpoint (CSS `.desktop-only` / media queries, no
`flex-wrap` reflow hack anymore).

**3. Route-based code splitting.** `App.tsx` now lazy-loads every route
except the landing page via `React.lazy`/`Suspense` (Ask, Citizen Dashboard,
Gov Dashboard, Auth pages, Content pages). Production build result:

| Chunk | Size (gzip) |
|---|---|
| `index` (landing + shared app shell) | 230.57 KB (78.61 KB) |
| `GovDashboard` (charts + map libs) | 389.48 KB (107.64 KB) |
| `SignalMap` (Leaflet) | 155.14 KB (45.51 KB) |
| `AskPage` | 3.56 KB (1.63 KB) |
| `ContentPages` | 2.76 KB (1.11 KB) |
| `AuthPages` | 2.32 KB (0.86 KB) |
| `CitizenDashboard` | 1.35 KB (0.70 KB) |

The heaviest dependencies (Leaflet, Recharts) now only load when a health
official actually opens the Government Dashboard, instead of shipping to
every citizen visiting the landing/Ask page.

**4. A real security gap found and fixed.** `POST /api/v1/auth/register`
previously accepted any `role` in the request body, so anyone could
self-register as `health_official` or `admin` — the frontend even exposed a
"Health Official" option in the sign-up form. Fixed:
- Backend now hard-rejects (`403`) any registration attempt where
  `role != citizen`; the DB write always forces `role=citizen` regardless.
- The frontend Register page's role selector was removed — public sign-up
  is citizen-only, with a note directing officials to contact an administrator.
- Privileged demo accounts (`official@demo.jagriti`, `admin@demo.jagriti`)
  are now provisioned directly by the seed script instead of through the
  public endpoint (see §6).
- Test suite updated: `test_signal_plane.py` / `test_e2e_demo_flow.py` now
  provision privileged test users directly against the DB (matching the
  seed script's pattern) instead of the public endpoint; a new assertion
  confirms `POST /auth/register {"role": "admin"}` returns `403`.

**5. Final validation results:**
- **Backend tests:** 21/21 passing (`pytest tests/ -v`), run twice — once
  right after the security fix, once again after all frontend changes.
- **Backend syntax:** every file under `app/` compiles cleanly (`py_compile`).
- **Frontend `npx tsc -b`:** zero errors.
- **Frontend `npm run build`:** succeeds, see chunk table above.
- **API consistency:** every `api.get`/`api.post` call site in the frontend
  cross-checked against the live FastAPI route table — zero mismatches.
- **Authentication/RBAC:** confirmed public registration is citizen-only;
  `health_official`/`admin` self-registration is rejected; all
  `/dashboard/*` and `/awareness/*` government routes require
  `Depends(require_roles(...))`; citizen-only routes require a valid token.
- **Privacy:** confirmed the government analytics layer (`/dashboard/trends`,
  `/dashboard/alerts`, `/dashboard/gov/overview`) only ever returns
  `topic_category`/`symptom_tag`, coarse `district`/`block_name`,
  `day_bucket`/`week_bucket`, and aggregate counts — the `SignalEvent` table
  has no `user_id`, `session_id`, `question_text`, or lat/lon columns at all,
  and `AnonymizedSymptomReport` aggregates are additionally suppressed below
  the k-anonymity threshold before ever reaching an endpoint.
- **Medical safety:** confirmed `MedicalSafetyEngine` hard-gates emergency
  and self-harm language before any AI generation (fixed, reviewed override
  messages, `block_ai_generation=True`), and that both `DemoAIService` and
  `GeminiAIService`'s system prompt explicitly forbid diagnosing an
  individual or confirming an outbreak.
- **Docker:** not tested — no Docker daemon is available in this sandbox.
  The `Dockerfile`s and `docker-compose.yml` were not modified in this pass,
  so their status is unchanged from prior sessions (structurally reviewed,
  not executed).

**Remaining, explicitly out of scope for this pass (per instructions):**
no WhatsApp/SMS/ABDM/ASHA integration, no advanced forecasting, no real
government system integration, no automated accessibility audit, no
production-grade rate limiting/monitoring — all future work, not needed for
the SIH demo.

---

## Session 5 — Infrastructure-only fix: migrations before seed

`docker-compose.yml`'s `backend` service previously seeded demo data without
ever running Alembic migrations, relying only on `Base.metadata.create_all()`
inside the seed script to create tables. Fixed the startup order to be
explicit and correct:

1. `db` becomes healthy (`pg_isready`, existing `depends_on: condition:
   service_healthy` — unchanged)
2. `alembic upgrade head` — applies all three migrations
3. `python -m app.db.seed` — seeds content + demo accounts (idempotent;
   still safe to re-run on every container restart)
4. `uvicorn app.main:app` — starts the API

Only `backend.command` in `docker-compose.yml` changed, from:
`sh -c "python -m app.db.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"`
to:
`sh -c "alembic upgrade head && python -m app.db.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"`

No application code, frontend, database models, or authentication logic was
touched. Verified:
- `docker-compose.yml` parses as valid YAML (`yaml.safe_load`).
- The backend `Dockerfile`'s `WORKDIR /app` matches where `alembic.ini` and
  the `alembic/` directory are copied to, so a bare `alembic upgrade head`
  resolves `script_location = alembic` correctly with no path changes needed.
- `alembic/env.py` already reads `DATABASE_URL` from `app.core.config.settings`
  (which reads the environment variable), so migrations correctly target the
  `db` service's Postgres instance, not a hardcoded URL.
- Ran the exact sequence (`alembic upgrade head` then `python -m app.db.seed`)
  against a clean throwaway database in this sandbox (no Docker daemon
  available here, so verified via a local DB rather than the container) — all
  three migrations applied cleanly, then all seed data (including the demo
  accounts from Session 4) populated with zero errors.
- Backend test suite re-run after this change: 21/21 passing (unaffected, as
  expected for an infra-only change).
- Docker itself still not tested end-to-end in this sandbox — no Docker
  daemon available here. This must be verified once on your Windows machine.
