"use client";

import Link from "next/link";
import { ScanLine, ShieldCheck, LogOut, UserRound, Trash2, X, Loader2, AlertCircle, LayoutGrid, ArrowRight } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "./theme-toggle";

export function Navbar() {
  const { officer, logout, deleteAccount } = useAuth();
  const router = useRouter();
  const [accountOpen, setAccountOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState<"logout" | "delete" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const navItems = [
    { label: "How it works", href: "/#how-it-works" },
    { label: officer ? "Dashboard" : "My scans", href: officer ? "/dashboard" : "/login?next=/dashboard" },
  ];

  async function handleLogout() {
    setError(null);
    setBusy("logout");
    try {
      await logout();
      router.refresh();
      router.replace("/login?next=/dashboard");
    } catch {
      setError("Could not sign out. Please try again.");
      setBusy(null);
    }
  }

  async function handleDeleteAccount() {
    if (confirmation !== "DELETE") return;
    setError(null);
    setBusy("delete");
    try {
      await deleteAccount();
      try {
        window.localStorage.removeItem("metrology-recent-scans");
      } catch {
        // Local cleanup is optional and must not block account deletion.
      }
      router.refresh();
      router.replace("/");
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Account deletion failed. Please try again.");
      setBusy(null);
    }
  }

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/85 backdrop-blur-xl transition-colors duration-300">
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 sm:px-8">
        <div className="flex items-center gap-3">
          <Link href="/" className="brand-mark" aria-label="Metrology Verify home">
            <ScanLine className="h-[18px] w-[18px] text-emerald-700 dark:text-emerald-300" strokeWidth={2.2} />
          </Link>
          <div className="leading-tight">
            <p className="font-display text-[15px] font-semibold text-ink-950 dark:text-paper-50">Metrology Verify</p>
            <p className="mt-0.5 font-mono text-[9px] uppercase tracking-[0.22em] text-ink-700/60 dark:text-paper-100/60">Label intelligence</p>
          </div>
        </div>

        <nav className="hidden items-center gap-7 md:flex" aria-label="Main navigation">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} className="text-sm font-medium text-ink-700 transition-colors hover:text-emerald-700 dark:text-paper-100/70 dark:hover:text-emerald-300">
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2.5">
          {officer && (
            <div className="hidden items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 shadow-sm sm:flex">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-700 dark:text-emerald-300" />
              <span className="font-mono text-[10px] text-ink-900/80 dark:text-paper-50/80">{officer.badgeId}</span>
            </div>
          )}
          <ThemeToggle />
          {officer ? (
            <div className="relative">
              <Button type="button" variant="ghost" size="sm" onClick={() => setAccountOpen((open) => !open)} aria-expanded={accountOpen} aria-label="Open account menu" className="text-ink-900 hover:bg-ink-900/5 dark:text-paper-50 dark:hover:bg-paper-50/10">
                <UserRound className="h-4 w-4" />
                <span className="hidden sm:inline">Account</span>
              </Button>
              {accountOpen && (
                <div className="absolute right-0 top-12 z-40 w-56 rounded-2xl border border-border bg-popover p-2 text-popover-foreground shadow-card">
                  <div className="flex items-center gap-2 rounded-xl bg-ink-900/[0.03] px-3 py-2 dark:bg-paper-50/[0.06]">
                    <LayoutGrid className="h-4 w-4 text-emerald-700 dark:text-emerald-300" />
                    <p className="truncate text-xs text-ink-700/70 dark:text-paper-100/70">{officer.name}</p>
                  </div>
                  <button type="button" disabled={busy !== null} onClick={handleLogout} className="mt-2 flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-left text-sm text-ink-800 hover:bg-ink-900/5 disabled:opacity-50 dark:text-paper-50 dark:hover:bg-paper-50/10"><LogOut className="h-4 w-4" />{busy === "logout" ? "Signing out..." : "Sign out"}</button>
                  <button type="button" disabled={busy !== null} onClick={() => { setAccountOpen(false); setDeleteOpen(true); setConfirmation(""); setError(null); }} className="flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-left text-sm text-clay-600 hover:bg-clay-50 disabled:opacity-50"><Trash2 className="h-4 w-4" />Delete account</button>
                </div>
              )}
            </div>
          ) : (
            <Link href="/login?next=/dashboard" className="inline-flex items-center gap-2 rounded-xl border border-ink-900/10 bg-surface px-3.5 py-2 text-sm font-medium text-ink-900 transition-colors hover:border-emerald-500/30 hover:bg-emerald-50 dark:border-paper-50/15 dark:bg-paper-50/5 dark:text-paper-50 dark:hover:border-emerald-300/30 dark:hover:bg-emerald-500/10">
              Sign in
              <ArrowRight className="h-4 w-4" />
            </Link>
          )}
        </div>
      </div>
      {error && !deleteOpen && <p role="alert" className="mx-auto max-w-7xl px-6 pb-2 text-right text-xs text-clay-600">{error}</p>}
      {deleteOpen && <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/60 px-5 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="delete-account-title">
        <div className="w-full max-w-md rounded-[1.5rem] border border-clay-500/30 bg-card p-6 shadow-hero sm:p-7">
          <div className="flex items-start justify-between gap-4"><div><p className="eyebrow text-clay-600">Danger zone</p><h2 id="delete-account-title" className="mt-2 font-display text-2xl font-semibold text-ink-950 dark:text-paper-50">Delete account</h2></div><button type="button" aria-label="Close delete account dialog" onClick={() => setDeleteOpen(false)} disabled={busy === "delete"} className="rounded-full p-2 text-ink-700/60 hover:bg-ink-900/5 dark:text-paper-100/60 dark:hover:bg-paper-50/10"><X className="h-4 w-4" /></button></div>
          <div className="mt-5 flex items-start gap-3 rounded-xl border border-clay-500/25 bg-clay-50 p-4 text-sm text-ink-800 dark:text-paper-100"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-clay-600" /><p>This permanently deletes your Supabase account. This action cannot be undone.</p></div>
          <label htmlFor="delete-confirmation" className="mt-5 block text-sm font-medium text-ink-950 dark:text-paper-50">Type DELETE to continue</label><input id="delete-confirmation" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} disabled={busy === "delete"} autoComplete="off" className="mt-2 h-11 w-full rounded-xl border border-ink-900/15 bg-canvas px-3 text-ink-950 outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100 dark:border-paper-50/15 dark:bg-paper-50/[0.06] dark:text-paper-50" />
          {error && <p role="alert" className="mt-3 text-sm text-clay-600">{error}</p>}
          <div className="mt-6 flex justify-end gap-3"><Button type="button" variant="outline" onClick={() => setDeleteOpen(false)} disabled={busy === "delete"} className="border-ink-900/15 text-ink-950 dark:border-paper-50/20 dark:text-paper-50">Cancel</Button><Button type="button" variant="destructive" onClick={handleDeleteAccount} disabled={confirmation !== "DELETE" || busy === "delete"}>{busy === "delete" ? <><Loader2 className="h-4 w-4 animate-spin" /> Deleting account...</> : <><Trash2 className="h-4 w-4" /> Delete account</>}</Button></div>
        </div>
      </div>}
    </header>
  );
}
