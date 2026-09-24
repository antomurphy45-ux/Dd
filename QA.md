# Construction Control — Consolidated QA Record

This file replaces the large collection of phase-specific QA markdown files. Historical QA has been consolidated here so the repository keeps one QA record instead of dozens of separate phase documents.

## Current phase — 32.43

### Objective
Diagnose the production Netlify Blobs credential problem without exposing secrets and align the implementation with the current Netlify Functions/Blobs runtime behaviour.

### Changes
- `/healthz` remains dependency-free and now reports only boolean presence information for relevant runtime variables.
- Added a phase marker `32.43` to the diagnostic response.
- API Blobs access now tries the documented zero-configuration `getStore()` path first.
- Explicit site/token credentials remain a fallback only when deliberately supplied through environment variables.
- No secret is stored in the repository.
- Consolidated README/QA/deployment documentation into `README.md` and `QA.md`.
- Removed obsolete phase-specific documentation files from the repository root.

### Validation
- JavaScript syntax: PASS
- Python compile: PASS
- Current Netlify readiness + Phase 32.43 diagnostic + production/security/function/routing/deployment tests: **29 passed**
- Netlify frontend build preparation: PASS
- Root/static/public frontend synchronisation: PASS
- Public output contains `index.html`, `app.js`, `app.css`: PASS

### Production verification status
**Pending upload/deploy.** The local environment cannot prove the live Netlify Function runtime or Netlify Blobs platform context.

---

# Historical QA

## Phase 32.2 — Daily Operating Sequence + DUB10/DUB50

Implemented Morning Brief, End-of-day Close Out, assignment-driven attendance, project dashboard health, DUB10/DUB50 seeded programmes, staff assignments and task-staff assignments.

Validation recorded at the time:
- Python compile: PASS
- JavaScript syntax: PASS
- Root/static asset synchronisation: PASS
- Phase 32.2 tests: 3/3 PASS
- DUB10/DUB50 tests: 2/2 PASS
- Combined selected regression set: 26/26 PASS
- Full historical suite was not claimed as clean because legacy tests retained older status/fixture assumptions.

## Phase 32.3 — Function/CRUD Repair

Unified task statuses, preserved legacy API compatibility, repaired task persistence, daily status inference, programme task persistence, modal handling and frontend synchronisation.

Validation:
- Full regression suite: 140 passed, 0 failed
- Python syntax: PASS
- JavaScript syntax: PASS
- Root/static assets: PASS
- Docker build-context simulation: PASS
- Physical browser clicking was not claimed because the validation environment blocked Chromium navigation.

## Phase 32.4 — Staff, Assignments, Access Ladder and Settings

Added staff/assignment editing, persistent company settings, Settings navigation, access-ladder seeding and staff restoration without deleting existing records.

Validation:
- Python compile: PASS
- JavaScript syntax: PASS
- Staff/assignment/settings/access-ladder integration: 9/9 PASS
- Root/static synchronisation: PASS

## Phase 32.5–32.7 — Professional theming

Settings theming was corrected and then constrained so company colours affect the application shell rather than semantic operational colours. Dashboard/RFI/risk/action/snag/approval colours remain distinct.

Validation recorded:
- Theme contract tests passed
- Staff/settings integration passed
- Python/JavaScript syntax passed
- Root/static synchronisation passed
- Full historical suite was not claimed where legacy expectations remained.

## Phase 32.8 — Staff Assignment → Daily Site Control

Project staff assignments became the source of truth for Daily Site Control attendance. Future assignments are excluded until their start date and the assignment role is displayed.

Validation:
- Python compile: PASS
- JavaScript syntax: PASS
- Assignment/date workflow: PASS
- Selected tests: 12 PASS
- Root/static assets: PASS

## Phase 32.9 — Persistent Data Protection

Strengthened SQLite persistence, added storage status/health controls, backup/restore protection and persistent-storage configuration for the then-used hosting model.

Validation:
- Persistence restart test: PASS
- Selected regression/integration set: 21 PASS
- Python compile: PASS
- Storage health guard: PASS

This phase is retained here as historical record; the current deployment target is Netlify.

## Phase 32.10–32.13 — DUB84

DUB84 was imported and validated with 264 programme activities, 60 source manpower days and idempotent seeding. A later packaging issue where the programme JSON was not copied into the deployment image was identified and corrected.

Validation recorded:
- DUB84 creation/plan/task checks: PASS
- 264 activities: PASS
- Date integrity: PASS
- 60 manpower days matched source schedule: PASS
- Idempotent seed: PASS
- DUB10/DUB50 preserved: PASS
- Selected suites: 22 and 6 passes respectively

## Phase 32.15 — Backup/Restore

Added administrator backup/restore, SQLite-consistent snapshots, upload inclusion, manifests, path validation, company validation and pre-restore backup protection.

Validation:
- Selected Phase 32 regression/integration suite: 26 PASS
- Backup/restore round trip: PASS
- Persistence: PASS
- DUB84 seed: PASS
- Theme/daily/assignment/security/production tests: PASS

## Phase 32.16–32.18 — Staff, programme editing and training

Added staff metadata and board presentation, programme editing/relocation/deletion controls, persistent staff training records and training-document handling.

Validation recorded:
- Staff board: PASS
- Programme editing: PASS
- Training CRUD: 16 PASS in the Phase 32.18 targeted run
- Python/JavaScript syntax: PASS
- Root/static assets: PASS

## Phase 32.19 — Programme controls and training documents

Programme actions were moved to the Gantt row, the repeated activity list was removed, and training records gained document upload/open/delete support. Unicode programme export was repaired.

Validation:
- Programme button execution: 1/1 PASS
- Training document upload: 1/1 PASS
- UI contract: 2/2 PASS
- Combined targeted result: 9/9 PASS

## Phase 32.20 — PM Daily Cockpit / RAG / External Approvals

Added project RAG reasons, PM daily brief, external approval watch list and approval documents.

Runtime checks recorded:
- `/healthz`: PASS
- Login: PASS
- Dashboard: PASS
- RAG reason: PASS
- External approval create/list/update: PASS
- Approval document upload: PASS

## Phase 32.21–32.22 — Programme tabs and calendar

Removed visible information icons while retaining hover help. Programme tools became local tabs and the calendar became a monthly Sunday-to-Saturday board with ISO week numbers, activity tabs, progress and exceptions.

Validation:
- JavaScript/Python syntax: PASS
- Programme tabs: 8 PASS
- Calendar targeted suite: 6 PASS
- Root/static synchronisation: PASS

## Phase 32.23 — Roles/UI

Updated the visible access ladder to Viewer → Site User → Foreman → Charge Hand → Construction Manager → Business Unit Lead → Company Director → Company Administrator. Removed the old Project Manager/Site Manager entries from the visible role list and migrated those login roles to Construction Manager.

Validation:
- Targeted role/UI/programme/staff/training/PM tests: 15 PASS
- Permission checks: PASS
- User DELETE endpoint was not exposed.

## Phase 32.24–32.27 — Dashboard boot repairs

Fixed sequential frontend boot errors involving `DASH_MODULES`, `dashboardProjectCards`, `dashValue`, `layout` and navigation. Root/static frontend copies remained synchronised.

Validation recorded across the phases:
- Python syntax: PASS
- JavaScript syntax: PASS
- Local health/login/dashboard smoke tests: PASS
- Targeted regression sets: 9–12 PASS per phase

## Phase 32.28 — Cache and persistence controls

Added frontend cache busting and explicit persistence controls in the then-current hosting package.

Validation:
- Phase 32.28 tests: 4 PASS
- Existing targeted tests: 16 PASS
- Persistence save/restart smoke: PASS
- ZIP integrity: PASS

## Phase 32.29 — Netlify-only architecture

Moved the production deployment model to Netlify:
- Static frontend on Netlify
- Netlify Functions for API/health
- Pyodide for the existing Python application logic
- Netlify Blobs for persistent SQLite and uploaded documents
- No Render runtime dependency

Validation recorded:
- Python/JavaScript syntax: PASS
- Netlify configuration: PASS
- Netlify adapter health/login smoke: PASS
- Settings persistence through fresh Python process: PASS
- Focused regression set: 22 PASS

## Phase 32.30–32.32 — Netlify build and login routing

Added `netlify-build.mjs`, explicit `public/` generation, API splat routing, health routing, JSON error handling and same-origin session-cookie handling.

Validation recorded:
- Build: PASS
- Public assets: PASS
- Netlify routing tests: PASS
- JavaScript/Python syntax: PASS

## Phase 32.33–32.36 — Netlify function discovery and handler compatibility

Iterated through Netlify Function entry-point layouts to remove handler-discovery ambiguity. The final current architecture uses modern ESM Function entries plus the official `@netlify/aws-lambda-compat` wrapper.

Validation recorded:
- Function entry syntax: PASS
- Lambda handler compatibility checks: PASS
- Python syntax: PASS
- ZIP integrity: PASS

## Phase 32.38 — Independent Netlify health probe

Added an independent dependency-free health function so function deployment could be verified before loading Pyodide. The API and health function were separated, and current Netlify readiness tests were established as the deployment gate.

Validation recorded:
- Function syntax: PASS
- Python syntax: PASS
- Current Netlify readiness: 7 PASS
- Production/security/current readiness: 16 PASS
- Direct local health invocation: PASS

## Phase 32.39–32.42 — Root function layout and Blobs investigation

The Function directory was moved to the repository root `functions/`, with `lib/` also at the root. This eliminated a deployment-directory mismatch. The independent `/healthz` endpoint subsequently returned HTTP 200 in production, proving that Netlify Functions were being deployed.

Production login then exposed a Netlify Blobs runtime problem. The code was changed to use the modern Netlify Functions runtime and the official Lambda compatibility wrapper, followed by an explicit credential fallback in Phase 32.42.

The latest production log still reported a missing `NETLIFY_AUTH_TOKEN`. Phase 32.43 changes the order of operations: documented automatic Netlify Blobs context is now tried first, with explicit credentials only as fallback, and `/healthz` exposes safe presence diagnostics.

## Test-gate policy

A phase is not considered complete merely because source code was changed. The phase must have:

1. Syntax validation.
2. Targeted regression tests.
3. Relevant application/API tests.
4. Asset synchronisation checks.
5. Build/package checks.
6. Production verification when the change depends on Netlify runtime behaviour.

Where a historical test suite contains stale assumptions from earlier phases, those failures are documented rather than silently reported as passes.
