import { Link } from "react-router-dom";
import { Logo, Wordmark } from "../components/Logo";
import { Badge } from "../components/ui/Badge";

const FEATURES = [
  {
    title: "Group expense engine",
    description: "Equal, exact, percentage, or share-weighted splits. Balances and simplified debts computed server-side, never trusted from the browser.",
  },
  {
    title: "Tamper-evident ledger",
    description: "Every financial action is SHA-256 hashed and chained to the one before it. Edit history straight in the database, and verification catches it.",
  },
  {
    title: "Role-based controls",
    description: "Owners, admins, and members see and do exactly what their role allows — enforced on the backend, not just hidden in the UI.",
  },
  {
    title: "Settlement intelligence",
    description: "A debt-simplification pass collapses chains of IOUs into the fewest transactions needed to settle a trip.",
  },
  {
    title: "Security Center",
    description: "Live audit-chain status, verification history, and authentication activity — pulled from real backend checks, never faked.",
  },
  {
    title: "Exportable reports",
    description: "CSV and PDF reports for expenses, balances, settlements, and the audit trail itself — ready to hand to anyone who asks.",
  },
];

export function Landing() {
  return (
    <div className="min-h-screen bg-grid">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <Logo />
          <Wordmark />
        </div>
        <nav className="hidden items-center gap-8 text-sm text-ink-soft md:flex">
          <a href="#platform" className="hover:text-ink">Platform</a>
          <a href="#security" className="hover:text-ink">Security</a>
          <Link to="/trips" className="hover:text-ink">Product</Link>
        </nav>
        <div className="flex items-center gap-3">
          <Link to="/login" className="text-sm text-ink-soft hover:text-ink">Log in</Link>
          <Link to="/register" className="btn-primary">Get started</Link>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl grid-cols-1 gap-10 px-6 py-14 md:grid-cols-2 md:py-20">
        <div>
          <span className="badge mb-6">
            Tamper-evident audit ledger · Built for transparency
          </span>
          <h1 className="font-serif text-5xl leading-[1.08] text-ink md:text-6xl">
            Expense sharing,
            <br />
            <span className="italic text-ink-soft">engineered</span> for trust.
          </h1>
          <p className="mt-6 max-w-md text-base leading-relaxed text-ink-soft">
            SplitSmart pairs group expense splitting with a cryptographically chained audit
            trail — built for trips, households, and teams who want to know their financial
            history can't quietly be rewritten.
          </p>
          <div className="mt-8 flex items-center gap-4">
            <Link to="/register" className="btn-primary">
              Create account
              <ArrowIcon />
            </Link>
            <Link to="/login" className="btn-secondary">Log in</Link>
          </div>
          <div className="mt-10 flex flex-wrap gap-x-6 gap-y-2 text-xs uppercase tracking-wide text-ink-faint">
            <span>SHA-256 chained ledger</span>
            <span>bcrypt password hashing</span>
            <span>Role-based access</span>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <span className="text-sm text-ink-soft">Goa Trip · 4 members</span>
            <Badge tone="green">Verified</Badge>
          </div>
          <div className="mt-4 font-serif text-4xl text-ink">₹ 21,640.00</div>
          <div className="text-sm text-ink-faint">Total tracked across the trip</div>

          <div className="mt-6 space-y-4 border-t border-line pt-4">
            {[
              { label: "Hotel (Tivoli Avenida)", by: "Paid by Krishiv", amount: "₹8,000.00" },
              { label: "Group dinner", by: "Paid by Rahul", amount: "₹4,800.00" },
              { label: "Scuba diving", by: "Paid by Aditya", amount: "₹6,000.00" },
            ].map((row) => (
              <div key={row.label} className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-ink">{row.label}</div>
                  <div className="text-xs text-ink-faint">{row.by}</div>
                </div>
                <div className="mono text-ink-soft">{row.amount}</div>
              </div>
            ))}
          </div>

          <div className="mt-5 rounded-lg bg-cream-soft p-3">
            <div className="mono text-ink-faint">audit: 0x9f3a…e1c2 ← 0x4b71…a8d0</div>
            <div className="mono mt-1 text-ink-faint">integrity: chain valid · 15 entries</div>
          </div>
        </div>
      </section>

      <section id="platform" className="border-t border-line bg-grid-soft">
        <div className="mx-auto max-w-7xl px-6 py-16">
          <span className="text-xs uppercase tracking-wide text-ink-faint">Platform</span>
          <h2 className="mt-2 max-w-2xl font-serif text-3xl text-ink md:text-4xl">
            Built for people who can't afford ambiguity about who owes what.
          </h2>
          <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="card p-6">
                <div className="mb-3 h-8 w-8 rounded-lg border border-line bg-cream-card" />
                <h3 className="font-serif text-lg text-ink">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-soft">{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="security" className="mx-auto max-w-7xl px-6 py-16">
        <div className="grid grid-cols-1 items-center gap-10 md:grid-cols-2">
          <div>
            <span className="text-xs uppercase tracking-wide text-ink-faint">Security</span>
            <h2 className="mt-2 font-serif text-3xl text-ink md:text-4xl">
              An expense app held to a security product's bar.
            </h2>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-ink-soft">
              Every register, login, expense, edit, void, and settlement is recorded as a
              chained, hashed audit event. Anyone on a trip can run verification and see the
              real result — VALID or COMPROMISED — straight from the backend.
            </p>
          </div>
          <div className="card grid grid-cols-2 gap-6 p-8">
            <Stat value="SHA-256" label="Chained audit hashing" />
            <Stat value="bcrypt" label="Password hashing" />
            <Stat value="RBAC" label="Owner / Admin / Member" />
            <Stat value="JWT" label="Access & refresh tokens" />
          </div>
        </div>
        <p className="mt-6 text-xs text-ink-faint">
          Security controls are implemented in-house, inspired by SOC 2 and ISO 27001
          principles. SplitSmart is not independently certified.
        </p>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-16">
        <div className="flex flex-col items-start justify-between gap-6 rounded-2xl bg-grid-dark px-8 py-10 text-cream-soft md:flex-row md:items-center">
          <div>
            <h3 className="font-serif text-2xl">Start tracking a trip in under a minute.</h3>
            <p className="mt-1 text-sm text-cream-soft/70">No credit card. Your first trip makes you the owner.</p>
          </div>
          <div className="flex gap-3">
            <Link to="/register" className="rounded-full bg-cream-soft px-5 py-2.5 text-sm font-medium text-ink hover:opacity-90">
              Create free account
            </Link>
            <Link to="/login" className="rounded-full border border-cream-soft/30 px-5 py-2.5 text-sm font-medium text-cream-soft hover:bg-white/5">
              Sign in
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-6 py-6 text-xs text-ink-faint md:flex-row">
          <div className="flex items-center gap-2">
            <Logo size={18} />
            <span>SplitSmart</span>
          </div>
          <div>SHA-256 chained audit log · bcrypt hashing · RBAC · © 2026 SplitSmart</div>
        </div>
      </footer>
    </div>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <div className="font-serif text-2xl text-ink">{value}</div>
      <div className="mt-1 text-xs uppercase tracking-wide text-ink-faint">{label}</div>
    </div>
  );
}

function ArrowIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
      <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
