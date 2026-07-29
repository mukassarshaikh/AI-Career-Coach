"use client";

/**
 * Navbar — top bar with user info and sign-out button.
 * Per frontend_architecture.md: /components/layout/Navbar
 */

import { signOut } from "next-auth/react";

interface NavbarProps {
  user: { name: string | null; email: string };
}

export function Navbar({ user }: NavbarProps) {
  return (
    <header className="h-14 border-b border-border bg-card px-6 flex items-center justify-between flex-shrink-0">
      <p className="text-sm text-muted-foreground">
        {/* Page title injected by each page's <h1> — Navbar shows user greeting */}
        Welcome, <span className="font-medium text-foreground">{user.name ?? user.email}</span>
      </p>
      <button
        id="sign-out-button"
        onClick={() => signOut({ callbackUrl: "/login" })}
        className="text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        Sign out
      </button>
    </header>
  );
}
