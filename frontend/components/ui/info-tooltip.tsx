"use client";

import { Info } from "lucide-react";
import { useState } from "react";

export function InfoTooltip({ label, children }: { label: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <span className="relative inline-flex">
      <button
        type="button"
        aria-label={label}
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
        className="inline-flex h-6 w-6 items-center justify-center rounded-full text-current/50 transition hover:bg-current/10 hover:text-current focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brass-400"
      >
        <Info className="h-3.5 w-3.5" />
      </button>
      {open && (
        <span role="tooltip" className="absolute right-0 top-8 z-20 w-60 rounded-xl border border-ink-900/10 bg-surface p-3 text-left text-xs leading-5 text-ink-700 shadow-card dark:border-paper-50/10 dark:bg-night-surface dark:text-paper-100">
          {children}
        </span>
      )}
    </span>
  );
}