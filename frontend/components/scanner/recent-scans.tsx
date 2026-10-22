"use client";

import { ChevronRight, History, ShieldAlert, ShieldCheck } from "lucide-react";
import { formatDateTime } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { ScanResponse } from "@/lib/types";

export function RecentScans({ scans, onOpen, onClear }: { scans: ScanResponse[]; onOpen: (scan: ScanResponse) => void; onClear?: () => void }) {
  if (!scans.length) return null;

  return (
    <section className="mt-12" aria-labelledby="recent-scans-heading">
      <div className="mb-4 flex items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Local register</p>
          <h2 id="recent-scans-heading" className="mt-1 font-display text-2xl font-semibold text-ink-900 dark:text-paper-50">Recent scans</h2>
        </div>
        <div className="flex items-center gap-3"><History className="h-5 w-5 text-teal-600" aria-hidden="true" />{onClear && <button type="button" onClick={onClear} className="text-xs font-medium text-ink-700/60 underline-offset-4 hover:text-coral-600 hover:underline dark:text-paper-100/60">Clear register</button>}</div>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        {scans.map((scan) => {
          const clean = scan.violations.length === 0;
          return (
            <button key={scan.id} type="button" onClick={() => onOpen(scan)} className="group flex min-h-24 items-center justify-between rounded-2xl border border-ink-900/10 bg-surface p-5 text-left shadow-card transition-all hover:-translate-y-0.5 hover:shadow-card-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brass-500 dark:border-paper-50/10 dark:bg-night-surface">
              <span className="min-w-0">
                <span className="flex items-center gap-2 font-mono text-xs text-ink-900/70 dark:text-paper-50/75">
                  {clean ? <ShieldCheck className="h-4 w-4 text-teal-600" /> : <ShieldAlert className="h-4 w-4 text-coral-600" />}
                  {clean ? "Clean label" : `${scan.violations.length} finding${scan.violations.length === 1 ? "" : "s"}`}
                </span>
                <span className="mt-2 block truncate text-xs text-ink-700/60 dark:text-paper-100/55">{formatDateTime(scan.created_at)}</span>
              </span>
              <ChevronRight className="h-4 w-4 shrink-0 text-ink-700/40 transition-transform group-hover:translate-x-0.5 dark:text-paper-100/40" />
            </button>
          );
        })}
      </div>
    </section>
  );
}
