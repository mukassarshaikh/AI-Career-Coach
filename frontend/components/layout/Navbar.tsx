"use client";

/**
 * Navbar — top header bar with user profile drawer/dropdown menu.
 * Groups Signed in User info, Sign out button, and GDPR Delete Account action.
 * Restyled matching design_system.md §5 & §6.
 */

import { useState, useRef, useEffect } from "react";
import { signOut } from "next-auth/react";
import { User, LogOut, Trash2, AlertTriangle, X, ChevronDown, ShieldAlert } from "lucide-react";
import { deleteUserAccount } from "@/lib/api/userApi";

interface NavbarProps {
  user: { name: string | null; email: string };
}

export function Navbar({ user }: NavbarProps) {
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const menuRef = useRef<HTMLDivElement>(null);

  // Derive user initials for profile badge avatar
  const displayName = user.name || user.email;
  const initials = user.name
    ? user.name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
    : user.email.slice(0, 2).toUpperCase();

  // Close profile dropdown menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsProfileMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleDeleteAccount = async () => {
    setIsDeleting(true);
    setErrorMsg(null);
    try {
      await deleteUserAccount();
      setIsConfirmOpen(false);
      await signOut({ callbackUrl: "/login" });
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to delete account. Please try again.");
      setIsDeleting(false);
    }
  };

  return (
    <>
      <header className="h-16 border-b border-line bg-paper-raised px-8 flex items-center justify-between flex-shrink-0 relative z-30">
        {/* Left header context / section indicator */}
        <div className="flex items-center gap-3">
          {/*<span className="text-body-sm font-medium text-ink-muted">AI Career Coach Platform</span>*/}
        </div>

        {/* Right profile menu trigger */}
        <div className="relative" ref={menuRef}>
          <button
            id="user-profile-menu-button"
            onClick={() => setIsProfileMenuOpen((prev) => !prev)}
            aria-expanded={isProfileMenuOpen}
            aria-haspopup="true"
            className="flex items-center gap-3 py-1.5 px-3 rounded-lg hover:bg-paper transition-colors cursor-pointer border border-transparent hover:border-line focus:outline-hidden focus:ring-2 focus:ring-forest/30"
          >
            <div className="w-8 h-8 rounded-full bg-forest text-paper-raised flex items-center justify-center font-mono text-body-sm font-bold shadow-xs">
              {initials}
            </div>
            <span className="text-body-sm font-medium text-ink hidden sm:inline-block max-w-[160px] truncate">
              {displayName}
            </span>
            <ChevronDown
              className={`w-4 h-4 text-ink-muted transition-transform duration-200 ${isProfileMenuOpen ? "rotate-180" : ""
                }`}
            />
          </button>

          {/* Profile Drawer / Dropdown Menu */}
          {isProfileMenuOpen && (
            <div
              className="absolute right-0 mt-2 w-72 bg-paper-raised border border-line rounded-xl shadow-lg p-4 z-40 animate-in fade-in zoom-in-95 duration-150"
              role="menu"
              aria-orientation="vertical"
              aria-labelledby="user-profile-menu-button"
            >
              {/* User Identity Header */}
              <div className="flex items-start gap-3 pb-3 border-b border-line">
                <div className="w-10 h-10 rounded-full bg-brass-soft/40 text-forest flex items-center justify-center font-mono text-body font-bold flex-shrink-0">
                  {initials}
                </div>
                <div className="overflow-hidden">
                  <p className="text-body-sm font-semibold text-ink truncate">
                    {user.name || "Candidate"}
                  </p>
                  <p className="text-data text-ink-muted font-mono truncate">{user.email}</p>
                  <span className="inline-block mt-1 text-[11px] font-medium text-forest bg-brass-soft/30 px-2 py-0.5 rounded-xs">
                    Signed in
                  </span>
                </div>
              </div>

              {/* Account Actions Group */}
              <div className="pt-2 space-y-1">
                {/* Sign Out Button */}
                <button
                  id="sign-out-button"
                  onClick={() => {
                    setIsProfileMenuOpen(false);
                    signOut({ callbackUrl: "/login" });
                  }}
                  role="menuitem"
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-body-sm font-medium text-ink-muted hover:text-ink hover:bg-paper transition-colors cursor-pointer text-left"
                >
                  <LogOut className="w-4 h-4 text-ink-muted" />
                  <span>Sign out</span>
                </button>

                {/* Delete Account Button (GDPR) */}
                <button
                  id="delete-account-button"
                  onClick={() => {
                    setIsProfileMenuOpen(false);
                    setErrorMsg(null);
                    setIsConfirmOpen(true);
                  }}
                  role="menuitem"
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-body-sm font-medium text-clay-alert hover:bg-clay-alert/10 transition-colors cursor-pointer text-left"
                  title="Delete your account and all associated data permanently"
                >
                  <Trash2 className="w-4 h-4 text-clay-alert" />
                  <span>Delete Account</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Account Deletion Confirmation Modal Dialog */}
      {isConfirmOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-ink/50 backdrop-blur-xs p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-account-modal-title"
        >
          <div className="bg-paper-raised border border-line rounded-xl max-w-md w-full p-6 shadow-xl relative animate-in fade-in zoom-in-95 duration-150">
            <button
              onClick={() => setIsConfirmOpen(false)}
              disabled={isDeleting}
              className="absolute top-4 right-4 text-ink-muted hover:text-ink transition-colors disabled:opacity-50 cursor-pointer"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-start gap-4 mb-4">
              <div className="p-3 bg-clay-alert/10 rounded-full text-clay-alert flex-shrink-0">
                <AlertTriangle className="w-6 h-6 text-clay-alert" />
              </div>
              <div>
                <h3 id="delete-account-modal-title" className="text-body font-semibold text-ink">
                  Permanently Delete Account?
                </h3>
                <p className="text-body-sm text-ink-muted mt-1">
                  This action is permanent and cannot be undone. All your uploaded resumes, parsed data,
                  skill gap reports, learning roadmaps, and chat history will be permanently erased.
                </p>
              </div>
            </div>

            {errorMsg && (
              <div className="mb-4 p-3 bg-clay-alert/10 border border-clay-alert/30 rounded-md text-body-sm text-clay-alert">
                {errorMsg}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 mt-6">
              <button
                type="button"
                onClick={() => setIsConfirmOpen(false)}
                disabled={isDeleting}
                className="px-4 py-2 text-body-sm font-medium text-ink-muted hover:text-ink transition-colors disabled:opacity-50 cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                id="confirm-delete-account-button"
                onClick={handleDeleteAccount}
                disabled={isDeleting}
                className="px-4 py-2 text-body-sm font-medium text-white bg-clay-alert hover:opacity-90 rounded-md transition-opacity disabled:opacity-50 cursor-pointer inline-flex items-center gap-2"
              >
                {isDeleting ? "Erasing Data..." : "Permanently Delete Account"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
