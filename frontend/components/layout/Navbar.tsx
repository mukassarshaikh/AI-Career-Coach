"use client";

/**
 * Navbar — top bar with user info and sign-out button.
 * Restyled matching design_system.md §5 & §6.
 */

import { signOut } from "next-auth/react";
import { LogOut } from "lucide-react";

interface NavbarProps {
  user: { name: string | null; email: string };
}

export function Navbar({ user }: NavbarProps) {
  return (
    <header className="h-16 border-b border-line bg-paper-raised px-8 flex items-center justify-between flex-shrink-0">
      <p className="text-body-sm text-ink-muted">
        Signed in as <span className="font-medium text-ink">{user.name ?? user.email}</span>
      </p>
      <button
        id="sign-out-button"
        onClick={() => signOut({ callbackUrl: "/login" })}
        className="inline-flex items-center gap-2 text-body-sm font-medium text-ink-muted hover:text-ink transition-colors cursor-pointer"
      >
        <LogOut className="w-4 h-4" />
        <span>Sign out</span>
      </button>
    </header>
  );
}
