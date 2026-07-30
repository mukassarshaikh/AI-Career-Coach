"use client";

/**
 * Sidebar — shared dashboard navigation.
 * Restyled matching design_system.md (§5 & §8 & §10).
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  BarChart2,
  Compass,
  MessageSquare,
} from "lucide-react";
import { Wordmark } from "./Wordmark";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/resume", label: "Resumes", icon: FileText },
  { href: "/skill", label: "Skill Gap", icon: BarChart2 },
  { href: "/learning", label: "Learning", icon: Compass },
  { href: "/career", label: "Career Advisor", icon: MessageSquare },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 flex-shrink-0 border-r border-line bg-paper-raised flex flex-col py-6 px-4">
      {/* Wordmark logo */}
      <div className="px-2 mb-8">
        <Wordmark />
      </div>

      {/* Navigation links */}
      <nav aria-label="Main navigation" className="flex-1">
        <ul className="space-y-1">
          {navItems.map(({ href, label, icon: Icon }) => {
            const isActive = pathname === href || pathname.startsWith(href + "/");
            return (
              <li key={href}>
                <Link
                  id={`nav-${label.toLowerCase().replace(/\s+/g, "-")}`}
                  href={href}
                  aria-current={isActive ? "page" : undefined}
                  className={`flex items-center gap-3 rounded-md px-3.5 py-2.5 text-body-sm font-medium transition-colors ${
                    isActive
                      ? "bg-brass-soft/40 text-forest font-semibold"
                      : "text-ink-muted hover:bg-paper hover:text-ink"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-forest" : "text-ink-muted"}`} />
                  <span>{label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
