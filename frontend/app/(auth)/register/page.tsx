"use client";

/**
 * Register page — (auth) route group, no sidebar/nav.
 * Restyled matching design_system.md (§1, §2, §3, §5, §6, §10).
 */

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Wordmark } from "@/components/layout/Wordmark";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      const res = await fetch(`${backendUrl}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data?.detail || "Account creation failed. Please check your inputs.");
        setLoading(false);
        return;
      }

      // Automatically sign in via NextAuth after successful registration
      const signInRes = await signIn("credentials", {
        redirect: false,
        email,
        password,
      });

      setLoading(false);

      if (signInRes?.error) {
        router.push("/login?registered=1");
      } else {
        router.push("/resume");
      }
    } catch {
      setError("Could not connect to the authentication server.");
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-paper px-6 py-12">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center space-y-3 flex flex-col items-center">
          <Wordmark className="mb-2" />
          <h1 className="font-display text-display-lg tracking-tight text-ink">
            Create your account
          </h1>
          <p className="font-body text-body-sm text-ink-muted">
            Start tracking your resume health, skill gaps, and career trajectory.
          </p>
        </div>

        <div className="rounded-xl border border-line bg-paper-raised p-8 shadow-sm space-y-6">
          <form id="register-form" onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div className="space-y-1.5">
              <label
                htmlFor="name"
                className="block font-body text-body-sm font-medium text-ink"
              >
                Full name
              </label>
              <input
                id="name"
                type="text"
                autoComplete="name"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-md border border-line bg-paper-raised px-3.5 py-2.5 text-body-sm text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-forest focus:border-transparent transition-all"
                placeholder="Jane Smith"
              />
            </div>

            <div className="space-y-1.5">
              <label
                htmlFor="reg-email"
                className="block font-body text-body-sm font-medium text-ink"
              >
                Email address
              </label>
              <input
                id="reg-email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-line bg-paper-raised px-3.5 py-2.5 text-body-sm text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-forest focus:border-transparent transition-all"
                placeholder="you@example.com"
              />
            </div>

            <div className="space-y-1.5">
              <label
                htmlFor="reg-password"
                className="block font-body text-body-sm font-medium text-ink"
              >
                Password
              </label>
              <input
                id="reg-password"
                type="password"
                autoComplete="new-password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-md border border-line bg-paper-raised px-3.5 py-2.5 text-body-sm text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-forest focus:border-transparent transition-all"
                placeholder="Min. 6 characters"
              />
            </div>

            {error && (
              <p role="alert" className="font-body text-body-sm font-medium text-clay-alert">
                {error}
              </p>
            )}

            <button
              id="register-submit"
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-forest px-4 py-2.5 font-body text-body-sm font-medium text-white shadow-sm hover:bg-forest-hover disabled:opacity-50 transition-colors cursor-pointer"
            >
              {loading ? "Creating account..." : "Create account"}
            </button>
          </form>

          <p className="text-center font-body text-body-sm text-ink-muted pt-2 border-t border-line">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-forest hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
