# SplitSmart

A secure group expense management platform. SplitSmart tracks who paid for what, calculates
who owes whom, and settles balances — like any expense-splitting app. What makes it different
is the layer underneath: **every financial and administrative action is recorded in a
cryptographically chained, tamper-evident audit ledger**, and the system can independently
verify — on demand — whether that history has been altered.

```
Record → Calculate → Settle → Cryptographically Audit → Verify Integrity
```

> Security controls in this project (password hashing, RBAC, the audit chain, rate limiting,
> etc.) are implemented in-house and inspired by SOC 2 / ISO 27001 principles. **SplitSmart is
> not independently certified** and makes no such claim.

## Table of contents

- [Architecture](#architecture)
- [Features](#features)
- [Tech stack](#tech-stack)
- [Database schema](#database-schema)
- [Security model](#security-model)
- [The audit chain, explained](#the-audit-chain-explained)
- [Setup](#setup)
- [Environment variables](#environment-variables)
- [Running the backend](#running-the-backend)
- [Running the frontend](#running-the-frontend)
- [Testing](#testing)
- [Demo data](#demo-data)
- [API overview](#api-overview)

## Architecture

```
SplitSmart/
├── backend/
│   ├── app/
│   │   ├── main.py           # app factory, middleware, exception handlers, routers
│   │   ├── config.py         # env-driven settings
│   │   ├── database.py       # SQLAlchemy engine/session
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── routers/          # FastAPI route handlers (thin; delegate to services)
│   │   ├── services/         # business logic: balances, splits, trips, settlements, reports
│   │   ├── audit/            # the cryptographic ledger: hashing, append, verification
│   │   ├── security/         # password hashing, JWT, RBAC deps, rate limiting
│   │   └── utils/            # canonical JSON, Decimal money helpers
│   ├── alembic/               # database migrations
│   ├── tests/                  # pytest suite
│   └── seed.py                  # demo data generator
└── frontend/
    ├── src/
    │   ├── api/                # axios client + typed per-domain API functions
    │   ├── components/          # shared UI, plus trip/ and expense/ and audit/ subfolders
    │   ├── pages/                # one component per route
    │   ├── context/               # AuthContext (in-memory access token, silent refresh)
    │   ├── types/                  # TS interfaces mirroring backend schemas
    │   └── utils/                   # formatting, RBAC helpers
    └── vite.config.ts                # dev proxy to the backend (see Security model)
```

The backend is the **sole source of truth** for money math, role checks, and integrity status.
The frontend never computes a balance, split, or permission decision on its own — it only
renders what the API returns. Nothing here is faked: every number on the dashboard, the
Security Center, and the Audit Ledger comes from a real database query or a real hash
verification pass.

## Features

- **Trips/groups** with members, roles, start/end dates, currency, archiving (soft-delete).
- **Expenses** with four split methods (equal, exact, percentage, shares), categories,
  filtering/search/sort, receipt attachments, and edit/void history — expenses are never hard
  deleted, only moved `ACTIVE → VOIDED` so the historical record stays intact.
- **Balance engine**: `net_balance = paid − owed + settlements_paid − settlements_received`,
  computed server-side per trip.
- **Debt simplification**: a greedy largest-debtor/largest-creditor match that collapses chains
  of IOUs into the minimum number of settling transactions.
- **Settlements** (`COMPLETED` / `CANCELLED`) that feed directly into the balance engine.
- **Role-based access control**: `OWNER` / `ADMIN` / `MEMBER`, enforced on the backend on every
  trip-scoped route — never inferred from the frontend.
- **Cryptographic audit ledger**: one global, append-only, SHA-256 hash-chained sequence of
  every register, login, trip/member/expense/settlement/role change, and report export.
- **Integrity verification**: walks the entire ledger from genesis, recomputes every hash, and
  reports `VALID` or `COMPROMISED` with the exact affected record.
- **Security Center**: live database/ledger status, verification history, integrity violation
  count, and recent authentication activity — all pulled from real endpoints.
- **Reports**: trip summary, member balances, settlement history, and audit activity, exportable
  as CSV (each type) and a one-page PDF summary.
- **Notifications**: in-app, generated for member adds, expenses, settlements, and role changes.
- **Receipts**: image/PDF upload with size/type validation, served only through an authenticated
  endpoint (no static file paths are ever exposed).

## Tech stack

**Backend** — Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, SQLite (dev) /
Postgres-compatible, passlib[bcrypt], PyJWT, slowapi (rate limiting), fpdf2 (PDF export),
pytest + httpx.

**Frontend** — React 18, TypeScript, Vite, React Router v6, @tanstack/react-query, axios,
Tailwind CSS, recharts, react-hot-toast.

## Database schema

| Table | Purpose |
|---|---|
| `users` | accounts, bcrypt-hashed passwords |
| `trips` | trip/group metadata, status (`ACTIVE`/`ARCHIVED`) |
| `trip_members` | membership + role (`OWNER`/`ADMIN`/`MEMBER`), status (`ACTIVE`/`REMOVED`) |
| `expenses` | amount, payer, category, split method, status (`ACTIVE`/`VOIDED`) |
| `expense_splits` | per-participant share of an expense |
| `settlements` | payer → receiver payments, status (`COMPLETED`/`CANCELLED`) |
| `audit_logs` | the append-only hash-chained ledger (see below) |
| `notifications` | in-app notifications per user |
| `receipts` | uploaded receipt metadata + server-side storage path |
| `refresh_tokens` | hashed, revocable refresh tokens for session rotation |
| `security_events` | operational signals (failed logins) — not part of the crypto chain |

Relationships: `User → TripMember → Trip → Expense → ExpenseSplit`, `Trip → Settlement`, and
every mutating action across all of the above `→ AuditLog`.

Schema is managed with Alembic migrations (`backend/alembic/`); the initial revision is included.

## Security model

- **Passwords**: bcrypt via passlib, never stored or logged in plaintext.
- **Sessions**: short-lived JWT access tokens (returned in the response body, kept in memory on
  the frontend — never `localStorage`) plus a rotating, revocable refresh token stored **hashed**
  in the database and set as an `httpOnly` cookie.
- **Same-site cookie note**: the Vite dev server proxies `/api/*` to the backend
  (`vite.config.ts`) so the frontend and API are same-origin in development — this is what lets
  the `SameSite=Lax` refresh cookie actually get sent. If you deploy frontend and backend on
  different origins in production, either keep them behind one reverse-proxy origin or adjust
  the cookie's `SameSite`/domain settings accordingly.
- **RBAC**: every trip-scoped route resolves the caller's role from `trip_members` via a FastAPI
  dependency — role, trip ownership, and user identity are always derived from the authenticated
  session server-side, never trusted from request bodies.
- **Input validation**: Pydantic schemas at every boundary; split math (equal/exact/percentage/
  shares) is validated and computed entirely server-side using `Decimal` arithmetic — amounts
  are never trusted from the client.
- **Rate limiting**: `/api/auth/login` and `/api/auth/register` are rate-limited (slowapi).
- **Headers**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` on every response;
  HSTS when `ENVIRONMENT=production`.
- **Errors**: unhandled exceptions are logged server-side and return a generic `500` — stack
  traces are never sent to the client.
- **File uploads**: receipts are content-type/size validated, stored under a server-controlled
  path, and served only via an authenticated endpoint that checks trip membership.

## The audit chain, explained

Every important action creates one row in the global `audit_logs` table:

```
current_hash = SHA256(event_type | actor_id | entity_id | timestamp | canonical(event_data) | previous_hash)
```

- The first record's `previous_hash` is a fixed genesis constant.
- Every later record's `previous_hash` is the previous record's `current_hash`.
- `event_data` is serialized once to canonical JSON (sorted keys, no whitespace) and that exact
  string — not a re-derived one — is what gets hashed and stored, so the hash can always be
  reproduced deterministically from the stored row.
- No router or service ever issues an `UPDATE`/`DELETE` against `audit_logs` — it is append-only
  by construction.

**Verification** (`POST /api/audit/verify`, or per-trip at `POST /api/trips/{id}/audit/verify`)
walks every record from genesis, recomputes each hash, and checks the `previous_hash` linkage.
It returns:

```json
{ "status": "VALID", "records_checked": 124, "broken_links": 0, "affected_record": null }
```

or, if a record was altered directly in the database (bypassing the app):

```json
{ "status": "COMPROMISED", "records_checked": 124, "broken_links": 1, "affected_record": 87 }
```

This is **tamper-evident, not tamper-proof**: a hash chain within a single database can always
be fully rewritten by someone with direct DB access who recomputes every downstream hash. What
it guarantees is that the application itself has no update/delete path for history, and that any
edit made outside the application — accidental or malicious, partial or careless — is detectable.
`backend/tests/test_tamper_detection.py` demonstrates this directly: it mutates a stored row via
the DB session (bypassing every service function) and asserts verification reports
`COMPROMISED` with the correct `affected_record`.

The ledger is **one global sequence**, not one per trip — that's the strongest integrity
guarantee, since any tampering anywhere breaks one verifiable chain. The Audit Ledger and
Security Center pages filter this ledger to what's relevant to you (your account's events, plus
every trip you belong to); "Run verification" always checks the *entire* ledger, since that's
the only way the result means anything.

## Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- (Nothing else — SQLite ships with Python, no external DB server needed for local dev.)

### Clone and configure

```bash
git clone <this-repo>
cd Splitsmart
cp .env.example backend/.env
cp .env.example frontend/.env   # only VITE_API_BASE_URL is read from here
```

Edit `backend/.env` and set a real `SECRET_KEY` (`python -c "import secrets; print(secrets.token_hex(32))"`).
The defaults otherwise work out of the box for local development.

## Environment variables

See [`.env.example`](.env.example) for the full list with comments. Backend reads from
`backend/.env`; frontend reads `VITE_API_BASE_URL` from `frontend/.env`. Never commit a real
`.env` file — both are gitignored.

## Running the backend

```bash
cd backend
python -m venv venv
./venv/Scripts/activate        # Windows; use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt

alembic upgrade head            # apply migrations
python seed.py                   # optional: create demo data (see below)

uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000/api`, with interactive docs at
`http://localhost:8000/docs`.

## Running the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The dev server proxies `/api/*` to `http://localhost:8000` (see
`vite.config.ts`) — keep the backend running on port 8000 for this to work.

## Testing

```bash
cd backend
pytest
```

Covers: registration/login/protected routes, RBAC (member vs admin vs owner), all four split
methods (including rounding-remainder correctness), the balance engine (reproduces the spec's
worked "Goa Trip" example), debt simplification (chain-collapsing and balance conservation),
settlement effects on balances, audit hash determinism, chain verification, and — critically —
tamper detection against a directly-mutated database row.

## Demo data

```bash
cd backend
python seed.py
```

This drops and recreates the local SQLite database, then creates a "Goa Trip" with four users,
five expenses across every split method, two settlements, and runs a verification pass — so the
Security Center and Audit Ledger have real data the moment you log in.

| Email | Password |
|---|---|
| krishiv@splitsmart.demo | Demo1234! |
| rahul@splitsmart.demo | Demo1234! |
| arjun@splitsmart.demo | Demo1234! |
| aditya@splitsmart.demo | Demo1234! |

## API overview

All routes are prefixed `/api`. Full interactive documentation (request/response schemas) is
available at `/docs` once the backend is running.

```
POST   /auth/register            POST   /auth/login              POST  /auth/refresh
POST   /auth/logout              GET    /auth/me                 PATCH /auth/me
POST   /auth/change-password

GET    /trips                    POST   /trips
GET    /trips/{id}                PUT   /trips/{id}               DELETE /trips/{id}  (archive)
GET    /trips/{id}/members        POST  /trips/{id}/members
PATCH  /trips/{id}/members/{uid}  DELETE /trips/{id}/members/{uid}

GET    /trips/{id}/expenses       POST  /trips/{id}/expenses
GET    /expenses/{id}             PUT   /expenses/{id}            POST /expenses/{id}/void
POST   /expenses/{id}/receipt     GET   /expenses/{id}/receipt

GET    /trips/{id}/balances       GET   /trips/{id}/debts

GET    /trips/{id}/settlements    POST  /trips/{id}/settlements
POST   /settlements/{id}/cancel

GET    /trips/{id}/audit          POST  /trips/{id}/audit/verify
GET    /audit                     POST  /audit/verify

GET    /security/overview

GET    /notifications             PATCH /notifications/{id}/read  POST /notifications/read-all

GET    /reports/{trip_id}
GET    /reports/{trip_id}/export/csv?type=expenses|balances|settlements|audit
GET    /reports/{trip_id}/export/pdf

GET    /dashboard
```
