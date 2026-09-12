<div align="center">

# 💸 SplitSmart

### Secure Group Expense Platform with a Tamper-Evident Audit Ledger

**SplitSmart** is a secure group expense management platform. It tracks who paid for what,
calculates who owes whom, and settles balances — like any expense-splitting app. What makes it
different is the layer underneath: **every financial and administrative action is recorded in a
cryptographically chained audit ledger**, and the system can independently verify — on demand —
whether that history has been altered.

<br>

![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-Strict-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-Build%20Tool-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)

<br>

![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge)
![SQLite](https://img.shields.io/badge/SQLite-Dev%20DB-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-48%20passing-success?style=for-the-badge)
![Audit](https://img.shields.io/badge/Audit-SHA--256%20Chained-red?style=for-the-badge)

</div>

---

## 🖥️ Product Preview

<p align="center">
  <img src="docs/hero.png" alt="SplitSmart dashboard" width="100%">
</p>

<p align="center">
  <i>Real data, computed by the backend — balances, category spend, and audit status shown here are never faked on the frontend.</i>
</p>

---

## 🧭 Why SplitSmart?

Most expense-splitting apps stop at "who owes whom." That's the easy part. The harder question —
the one that actually matters when money and trust are involved — is:

> **Can the financial history be trusted? Has anything been quietly changed?**

A normal app has no answer to that. If an expense amount gets edited after the fact — by a bug, a
careless admin, or someone with direct database access — there's no way to ever know it happened.

**SplitSmart is built audit-first.** Every register, login, expense, edit, void, settlement, and
role change is chained into a single cryptographic ledger. Anyone in the app can hit "verify" and
get a real, backend-computed answer: `VALID` or `COMPROMISED`.

### Core Principles

- **Transparency** — every balance is traceable back to the expenses and splits that produced it
- **Accountability** — every action records who did it and when, enforced by the backend, not the UI
- **Auditability** — a full, append-only history of every financial and administrative event
- **Integrity** — tamper-evidence via a SHA-256 hash chain, independently verifiable at any time
- **Correctness** — split math, balances, and roles are computed and enforced server-side only

---

## ✨ Features

### 💰 Smart Expense Splitting

- Create trips/groups, add and remove members, assign **Owner / Admin / Member** roles
- Record expenses with description, amount, category, date, and notes
- Four split methods, all validated server-side:
  - **Equal** — divided evenly, remainder cents distributed deterministically
  - **Exact** — explicit per-person amounts, must sum exactly to the total
  - **Percentage** — per-person percentages, must sum to 100%
  - **Shares** — weighted split (e.g. 2:2:1:1)
- Backend balance engine computes `net = paid − owed + settlements_paid − settlements_received`
  per member — never trusted from the frontend
- Greedy debt-simplification collapses chains of IOUs into the fewest transactions needed to
  settle a trip (A→B→C collapses to a single A→C where possible)

### 🧾 Receipts & Settlements

- Attach a receipt (image or PDF, size/type validated) to any expense, served only through an
  authenticated endpoint scoped to trip membership — never a raw file path
- Record settlements between members, with cancellation support (creator or admin/owner only)
- Expenses and settlements are **voided, never deleted** (`ACTIVE → VOIDED`) — financial history
  stays intact for the audit trail

### 📊 Financial Dashboard

- Total spending, active trip count, amount you owe vs. amount owed to you
- Per-trip totals, category breakdown, recent expenses and settlements
- Every number comes from a real API call — nothing is hardcoded or estimated client-side

### 🔐 Secure Audit Ledger

Every important action is written to an append-only ledger:

```text
USER_REGISTERED · USER_LOGIN · USER_LOGOUT · PASSWORD_CHANGED
TRIP_CREATED · TRIP_UPDATED · TRIP_ARCHIVED
MEMBER_ADDED · MEMBER_REMOVED · ROLE_CHANGED
EXPENSE_CREATED · EXPENSE_UPDATED · EXPENSE_VOIDED
SETTLEMENT_CREATED · SETTLEMENT_CANCELLED
REPORT_GENERATED · AUDIT_VERIFICATION_RUN
```

There is no update/delete route for this table anywhere in the app — it is append-only by
construction. Edits to an expense record *both* the previous and new state in the same event.

### 🔗 Cryptographically Chained Audit Trail

Each ledger entry hashes itself together with the hash of the entry before it:

```text
Event A  (previous_hash = GENESIS)
   │
   ▼
current_hash = SHA256(type ⧺ actor ⧺ entity ⧺ timestamp ⧺ data ⧺ previous_hash)
   │
   ▼
Event B  (previous_hash = Event A's current_hash)
   │
   ▼
current_hash = SHA256( ... ⧺ previous_hash )
   │
   ▼
Event C  (previous_hash = Event B's current_hash)
```

**Verification** walks the entire chain from genesis, recomputes every hash, and checks each
`previous_hash` link. If a single field of a single historical record is edited directly in the
database, the very next verification reports `COMPROMISED` — and names the exact record. This is
tested: `backend/tests/test_tamper_detection.py` mutates a row directly via the DB session,
bypassing the app entirely, and asserts the chain reports the break.

### 🛡️ Security Center

- Live database and audit-chain status, pulled from a real check on every page load
- Total audit events, last verification time, integrity violation count
- Your recent authentication activity and a manual "Run verification" button
- A dedicated **Audit Ledger** page: the raw, paginated, filterable event table with truncated
  hashes

### 🔑 Authentication & Access Control

- Passwords hashed with **bcrypt**; JWT access tokens (short-lived) + rotating, revocable refresh
  tokens (httpOnly cookie, hashed at rest)
- Role-based access control — **Owner / Admin / Member** — enforced on every trip-scoped backend
  route, never inferred from the frontend
- Rate limiting on login/register, sanitized error responses (no stack traces or secrets leaked),
  strict CORS, standard security headers

### 📑 Reports

- Per-trip summary: totals, member balances, category breakdown, settlement history
- CSV export for expenses, balances, settlements, and the audit trail itself
- One-page PDF summary export

---

## ⚙️ How SplitSmart Works

```text
                         USER (browser)
                              │
                              ▼
                  React + TypeScript Frontend
                    (Vite dev proxy → /api)
                              │
                              ▼
                         FastAPI Backend
                              │
        ┌──────────┬──────────┼──────────┬──────────┐
        ▼          ▼          ▼          ▼          ▼
     Trips     Expenses   Settlements  Reports  Notifications
        │          │          │          │          │
        └──────────┴────┬─────┴──────────┴──────────┘
                         ▼
                  Balance Engine +
              Debt Simplification
                         │
                         ▼
                   Audit Service
            (SHA-256 hash chain, append-only)
                         │
                         ▼
              SQLite (dev) / PostgreSQL-ready
                         │
                         ▼
          Security Center · Audit Ledger · Dashboard
```

---

## 🔄 Application Workflow

```text
Register / Log in
        ↓
Create Trip  (you become OWNER)
        ↓
Add Members  (by email, assign role)
        ↓
Record Expense  (choose payer, split method, participants)
        ↓
Backend validates split & computes shares
        ↓
Balances recalculated (paid − owed + settlements)
        ↓
Audit Event Written & Chained  (hash = f(data, previous_hash))
        ↓
Settle Up  (record settlement, optionally simplified)
        ↓
Run Verification  →  VALID or COMPROMISED
```

---

## 🏗️ System Architecture

```text
┌───────────────────────────────────────────────────┐
│                 REACT + TYPESCRIPT                 │
│                                                     │
│  Dashboard · Trips · Expenses · Balances           │
│  Settlements · Security Center · Audit Ledger      │
│  Reports · Settings                                │
└────────────────────────┬────────────────────────────┘
                         │ REST (axios, silent refresh)
                         ▼
┌───────────────────────────────────────────────────┐
│                   FASTAPI BACKEND                  │
│                                                     │
│  routers/  → HTTP layer, auth deps, RBAC guards    │
│  services/ → business logic (balances, splits,     │
│              debt simplification, trips, reports)  │
│  security/ → password hashing, JWT, refresh tokens │
│  audit/    → hash chain, append, verify            │
└──────────┬──────────────────────────┬───────────────┘
           ▼                          ▼
┌────────────────────┐     ┌───────────────────────┐
│   RELATIONAL DB     │     │      AUDIT LEDGER      │
│  (SQLite / Postgres) │     │  (same DB, own table)  │
│                     │     │                        │
│ users, trips,        │     │ event_type, actor_id   │
│ trip_members,        │     │ entity, event_data     │
│ expenses, splits,    │     │ previous_hash          │
│ settlements,         │     │ current_hash           │
│ notifications         │     │ (append-only)          │
└────────────────────┘     └───────────────────────┘
```

---

## 🔐 Security Model

SplitSmart's security model is built around **traceability, integrity, and least-privilege
access** — implemented in-house, inspired by (but not certified against) SOC 2 / ISO 27001
principles. See the [Disclaimer](#️-disclaimer) below.

### Audit Record Shape

```text
AuditLog
├── id
├── event_type        e.g. EXPENSE_VOIDED
├── actor_id           who did it
├── trip_id            which trip (nullable — account-level events)
├── entity_type/id      what was acted on
├── event_data         canonical JSON (previous + new state for edits)
├── timestamp
├── previous_hash       ← the entry before it
└── current_hash        SHA256(everything above)
```

### What's enforced, and where

| Concern | Enforced by |
|---|---|
| Passwords | bcrypt via `passlib`, never stored or logged in plaintext |
| Sessions | JWT access token + rotating opaque refresh token (hashed at rest, httpOnly cookie) |
| Authorization | Per-request RBAC dependency, resolved from the DB — never from the request body |
| Split totals & balances | Recomputed server-side from `Decimal` math — frontend values are advisory only |
| Audit integrity | SHA-256 chain, append-only table, no update/delete code path exists |
| Uploads | Content-type allowlist, size limit, served via authenticated route only |
| Brute force | Rate limiting on `/auth/login` and `/auth/register` |

---

## 💻 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript |
| Build Tool | Vite |
| Styling | Tailwind CSS |
| Data fetching | TanStack Query (React Query) |
| Routing | React Router |
| Charts | Recharts |
| Backend | Python 3.11+ |
| API Framework | FastAPI |
| Validation | Pydantic v2 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Database | SQLite (dev) — PostgreSQL-compatible schema |
| Auth | JWT + bcrypt (passlib) |
| Audit System | SHA-256 cryptographic hash chain |
| Testing | pytest (48 tests) |
| Version Control | Git + GitHub |

---

## 📁 Project Structure

```text
SplitSmart/
│
├── backend/
│   ├── app/
│   │   ├── main.py              # app factory, middleware, routers
│   │   ├── config.py            # env-driven settings
│   │   ├── database.py          # engine/session
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routers/             # HTTP layer per domain
│   │   ├── services/            # balance engine, splits, trips, reports
│   │   ├── security/            # password hashing, JWT, RBAC, tokens
│   │   ├── audit/                # hash chain, append, verify
│   │   └── utils/                # money math, canonical JSON
│   ├── alembic/                  # migrations
│   ├── tests/                    # 48 pytest tests
│   ├── seed.py                    # demo data generator
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/                   # typed API client per domain
│   │   ├── components/            # shared UI, tabs, modals
│   │   ├── pages/                 # route-level pages
│   │   ├── context/                # AuthContext
│   │   ├── types/                  # TS interfaces mirroring backend schemas
│   │   └── utils/                   # formatting, role helpers
│   ├── vite.config.ts               # dev proxy → backend, same-origin cookies
│   └── package.json
│
├── docs/
│   └── hero.png
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Nothing else — SQLite ships with Python, no external DB server needed for local dev

### 1. Clone and configure

```bash
git clone https://github.com/KrishivSharma45/Splitsmart.git
cd Splitsmart
cp .env.example backend/.env
cp .env.example frontend/.env   # only VITE_API_BASE_URL is read from here
```

Edit `backend/.env` and set a real `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Backend

```bash
cd backend
python -m venv venv
./venv/Scripts/activate          # Windows; use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt

alembic upgrade head              # apply migrations
python seed.py                     # optional: create demo data

uvicorn app.main:app --reload --port 8000
```

API at `http://localhost:8000/api` — interactive docs at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The dev server proxies `/api/*` to the backend (see
`vite.config.ts`) so the refresh-token cookie stays same-site — keep the backend running on port
8000.

### Demo login

If you ran `python seed.py`:

| Email | Password |
|---|---|
| krishiv@splitsmart.demo | Demo1234! |
| rahul@splitsmart.demo | Demo1234! |
| arjun@splitsmart.demo | Demo1234! |
| aditya@splitsmart.demo | Demo1234! |

---

## 🔌 API Architecture

```text
React Component
      │
      ▼
Typed API module (frontend/src/api/*.ts)
      │
      ▼
FastAPI Router  →  RBAC dependency  →  current_user
      │
      ▼
Service layer (business logic, Decimal math)
      │
      ▼
SQLAlchemy  →  SQLite / PostgreSQL
      │
      ▼
Audit event appended to the hash chain
```

All routes are prefixed `/api`; full interactive request/response schemas are available at
`/docs` once the backend is running. Representative endpoints:

```text
POST /auth/register            POST /auth/login             POST /auth/refresh
POST /auth/logout              GET  /auth/me                 PATCH /auth/me

GET  /trips                     POST /trips
GET  /trips/{id}                 PUT  /trips/{id}              DELETE /trips/{id}  (archive)
POST /trips/{id}/members          PATCH/DELETE /trips/{id}/members/{uid}

GET/POST /trips/{id}/expenses      PUT /expenses/{id}           POST /expenses/{id}/void
POST/GET /expenses/{id}/receipt

GET  /trips/{id}/balances          GET  /trips/{id}/debts

GET/POST /trips/{id}/settlements    POST /settlements/{id}/cancel

GET  /trips/{id}/audit               POST /trips/{id}/audit/verify
GET  /audit                            POST /audit/verify

GET  /security/overview
GET  /reports/{trip_id}                 GET /reports/{trip_id}/export/csv|pdf
GET  /dashboard
```

---

## 📊 Example Expense Flow

```text
Expense Created
      │
      ├── description, amount, currency
      ├── paid_by (must be an active trip member)
      ├── category, date, notes
      └── split_method + participants
             │
             ▼
   Backend validates & computes shares
   (equal / exact / percentage / shares —
    never trusted from the frontend)
             │
             ▼
       Balances recalculated
             │
             ▼
   EXPENSE_CREATED audit event written,
   chained to previous_hash
             │
             ▼
     Dashboard, balances, and debts
        reflect the new state
```

---

## 🧪 Testing & Validation

```bash
cd backend
pytest
```

**48 tests**, covering:

- Registration, login, protected routes, password change
- RBAC — member vs. admin vs. owner, including "can't remove the only owner" and
  "only an owner can grant OWNER"
- All four split methods, including rounding-remainder correctness (e.g. splitting ₹100 three
  ways sums back to exactly ₹100.00)
- The balance engine — reproduces the spec's worked "Goa Trip" example exactly
- Debt simplification — chain-collapsing (A→B→C nets to a single A→C) and balance conservation
- Settlement effects on balances
- Audit hash determinism and full-chain verification
- **Tamper detection** — a test directly mutates an `audit_logs` row via the DB session, bypassing
  every service function, and asserts verification reports `COMPROMISED` with the exact affected
  record

### Development validation flow

```text
Implement  →  pytest  →  tsc --build  →  Verify in browser  →  Commit  →  Push
```

---

## 🗺️ Roadmap

### Expense Intelligence

- [ ] OCR-assisted receipt extraction (assistive only — never auto-trusted into financial values)
- [ ] AI-powered expense categorization suggestions
- [ ] Recurring expenses

### Analytics

- [ ] Historical spending trends across trips
- [ ] Exportable multi-trip reports

### Platform

- [ ] PostgreSQL deployment guide
- [ ] Email notifications alongside in-app ones
- [ ] Two-factor authentication
- [ ] Cloud deployment (containerized)

---

## 🎯 Project Goals

SplitSmart explores the intersection of:

- 💰 Expense Management
- 🔐 Applied Security (auth, RBAC, cryptographic integrity)
- 🔗 Auditability & Tamper-Evidence
- 📊 Financial Correctness (server-side money math, tested)
- ⚙️ Full-Stack Engineering (FastAPI + React/TypeScript)

The goal: shared expenses that are **transparent, correct, and provably untampered.**

---

## ⚠️ Disclaimer

SplitSmart implements security controls (password hashing, RBAC, JWT sessions, rate limiting, a
cryptographic audit chain) **in-house**, inspired by SOC 2 / ISO 27001 principles. **It is not
independently certified against SOC 2, ISO 27001, or any other standard**, and makes no such
claim.

The audit chain is **tamper-evident, not tamper-proof**: it detects edits made through or around
the application (including direct database edits) that don't also correctly recompute every
downstream hash. A person with full, sustained database access who recomputed the entire forward
chain could still evade detection — the same fundamental limit any single-database hash chain
has. This is a demonstration/portfolio project, not an audited production security product;
financial and security-critical decisions should not be based on it as-is.

---

## 👨‍💻 Author

**Krishiv Sharma**

B.Tech CSE — Cybersecurity

Interested in:

**Cybersecurity • Software Engineering • AI • Secure Systems**

---

<div align="center">

### 💸 SplitSmart

**Transparent Expenses · Tamper-Evident Records · Verifiable Trust**

Built with a focus on **Security · Auditability · Full-Stack Engineering**

⭐ If you found SplitSmart interesting, consider starring the repository.

</div>
