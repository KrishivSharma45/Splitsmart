import { Link } from "react-router-dom";
import { Logo } from "../Logo";

export function AuthSplitLayout({
  eyebrow,
  headline,
  tagline,
  children,
}: {
  eyebrow: string;
  headline: React.ReactNode;
  tagline: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid min-h-screen grid-cols-1 md:grid-cols-2">
      <div className="relative hidden flex-col justify-between bg-grid-dark px-12 py-10 text-cream-soft md:flex">
        <Link to="/" className="flex items-center gap-2">
          <Logo />
          <span className="font-serif text-lg text-cream-soft">
            SplitSmart<span className="text-cream-soft/50">.</span>
          </span>
        </Link>

        <div className="max-w-md">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-cream-soft/20 bg-cream-soft/5 px-3 py-1 text-xs uppercase tracking-wide text-cream-soft/70">
            <span className="h-1.5 w-1.5 rounded-full bg-accent-green" />
            {eyebrow}
          </span>
          <h1 className="mt-6 font-serif text-4xl leading-[1.15] text-cream-soft">{headline}</h1>
          <p className="mt-4 text-sm leading-relaxed text-cream-soft/60">{tagline}</p>
        </div>

        <div className="text-xs uppercase tracking-wide text-cream-soft/40">
          SHA-256 chained audit log · bcrypt hashing · RBAC
        </div>
      </div>

      <div className="flex items-center justify-center bg-grid-white px-6 py-12">
        <div className="w-full max-w-sm">
          <Link to="/" className="mb-8 flex items-center justify-center gap-2 md:hidden">
            <Logo />
            <span className="font-serif text-lg text-ink">
              SplitSmart<span className="text-ink-faint">.</span>
            </span>
          </Link>
          {children}
        </div>
      </div>
    </div>
  );
}
