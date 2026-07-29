"use client";

/**
 * Sidebar — shared dashboard navigation.
 * Per frontend_architecture.md: /components/layout/Sidebar
 */

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: "🏠" },
  { href: "/resume", label: "Resumes", icon: "📄" },
  { href: "/skill", label: "Skill Gap", icon: "📊" },
  { href: "/learning", label: "Learning", icon: "🗺️" },
  { href: "/career", label: "Career Advisor", icon: "💬" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 flex-shrink-0 border-r border-border bg-card flex flex-col py-6 px-3">
      {/* Logo */}
      <Link href="/dashboard" className="flex items-center gap-2 px-3 mb-8">
        <span className="text-primary text-xl font-bold">AI Career</span>
      </Link>

      {/* Nav links */}
      <nav aria-label="Main navigation">
        <ul className="space-y-1">
          {navItems.map(({ href, label, icon }) => {
            const isActive = pathname === href || pathname.startsWith(href + "/");
            return (
              <li key={href}>
                <Link
                  id={`nav-${label.toLowerCase().replace(/\s+/g, "-")}`}
                  href={href}
                  aria-current={isActive ? "page" : undefined}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                >
                  <span aria-hidden="true">{icon}</span>
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
