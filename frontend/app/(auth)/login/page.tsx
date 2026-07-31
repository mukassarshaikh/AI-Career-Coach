"use client";

/**
 * Login page — (auth) route group, no sidebar/nav.
 * Restyled matching design_system.md (§1, §2, §3, §5, §6, §10).
 */

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Wordmark } from "@/components/layout/Wordmark";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const registered = searchParams?.get("registered");
  const callbackUrl = searchParams?.get("callbackUrl") || "/resume";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const res = await signIn("credentials", {
      redirect: false,
      email,
      password,
    });

    setLoading(false);

    if (res?.error) {
      setError("Invalid email address or password. Verify your details and try again.");
    } else {
      window.location.href = callbackUrl;
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-paper px-6 py-12">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center space-y-3 flex flex-col items-center">
          <Wordmark className="mb-2" />
          <h1 className="font-display text-display-lg tracking-tight text-ink">
            Sign in to your account
          </h1>
          <p className="font-body text-body-sm text-ink-muted">
            Access your resume health score, skill-gap analysis, and career trajectory.
          </p>
        </div>

        {registered && (
          <div className="rounded-md bg-brass-soft/50 border border-brass p-3 text-body-sm text-ink text-center">
            Account created successfully. Sign in with your credentials below.
          </div>
        )}

        <div className="rounded-xl border border-line bg-paper-raised p-8 shadow-sm space-y-6">
          <form id="login-form" onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div className="space-y-1.5">
              <label
                htmlFor="email"
                className="block font-body text-body-sm font-medium text-ink"
              >
                Email address
              </label>
              <input
                id="email"
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
                htmlFor="password"
                className="block font-body text-body-sm font-medium text-ink"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-md border border-line bg-paper-raised px-3.5 py-2.5 text-body-sm text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-forest focus:border-transparent transition-all"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <p role="alert" className="font-body text-body-sm font-medium text-clay-alert">
                {error}
              </p>
            )}

            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-forest px-4 py-2.5 font-body text-body-sm font-medium text-white shadow-sm hover:bg-forest-hover disabled:opacity-50 transition-colors cursor-pointer"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p className="text-center font-body text-body-sm text-ink-muted pt-2 border-t border-line">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="font-medium text-forest hover:underline">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
