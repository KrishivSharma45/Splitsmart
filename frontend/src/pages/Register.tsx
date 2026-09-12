import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { extractErrorMessage } from "../api/client";
import { AuthSplitLayout } from "../components/auth/AuthSplitLayout";
import { useAuth } from "../context/AuthContext";

export function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register(email, fullName, password);
      navigate("/dashboard");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthSplitLayout
      eyebrow="Audit-ready"
      headline="Split expenses with a paper trail no one can quietly edit."
      tagline="Every trip, member, expense, and settlement you create becomes a chained, hashed audit event from the moment you sign up."
    >
      <h1 className="font-serif text-2xl text-ink">Create your account</h1>
      <p className="mt-1 text-sm text-ink-faint">Start tracking expenses in minutes.</p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label className="label" htmlFor="full_name">
            Full name
          </label>
          <input
            id="full_name"
            required
            autoComplete="name"
            className="input"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            autoComplete="new-password"
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <p className="mt-1 text-xs text-ink-faint">
            At least 8 characters, with an uppercase letter, lowercase letter, and a digit.
          </p>
        </div>

        {error && <p className="text-sm text-accent-red">{error}</p>}

        <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
          {isSubmitting ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-ink-faint">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-ink hover:underline">
          Log in
        </Link>
      </p>
    </AuthSplitLayout>
  );
}
