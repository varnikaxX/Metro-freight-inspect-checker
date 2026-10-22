"use client";

import { Check, X, Info, ChevronDown } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { getFieldConfig } from "@/lib/field-config";
import type { FieldDetail } from "@/lib/types";

export function FieldCard({ field }: { field: FieldDetail }) {
  const [open, setOpen] = useState(false);
  const cfg = getFieldConfig(field.field_name);
  const Icon = cfg.icon;
  const state = field.verification_state ?? (field.is_present ? "verified_present" : "not_detected_needs_review");

  const palette = {
    verified_present: {
      shell: "border-success/30 bg-success-surface",
      accent: "bg-success",
      iconWrap: "bg-success/15 text-accent-foreground",
      badge: "bg-success text-primary-foreground",
      status: "Verified",
    },
    verified_missing: {
      shell: "border-danger/30 bg-danger-surface",
      accent: "bg-danger",
      iconWrap: "bg-danger/15 text-danger",
      badge: "bg-danger text-primary-foreground",
      status: "Missing",
    },
    needs_review: {
      shell: "border-warning/30 bg-warning-surface",
      accent: "bg-warning",
      iconWrap: "bg-warning/15 text-secondary-foreground",
      badge: "bg-warning text-primary-foreground",
      status: "Needs review",
    },
    not_detected_needs_review: {
      shell: "border-warning/30 bg-warning-surface",
      accent: "bg-warning",
      iconWrap: "bg-warning/15 text-secondary-foreground",
      badge: "bg-warning text-primary-foreground",
      status: "Needs review",
    },
    not_assessed: {
      shell: "border-border bg-neutral-surface",
      accent: "bg-muted-foreground/30",
      iconWrap: "bg-muted text-muted-foreground",
      badge: "bg-muted text-muted-foreground",
      status: "Not assessed",
    },
    not_applicable: {
      shell: "border-border bg-neutral-surface",
      accent: "bg-muted-foreground/30",
      iconWrap: "bg-muted text-muted-foreground",
      badge: "bg-muted text-muted-foreground",
      status: "Not applicable",
    },
    default: {
      shell: "border-border bg-card",
      accent: "bg-muted-foreground/30",
      iconWrap: "bg-muted text-muted-foreground",
      badge: "bg-muted text-muted-foreground",
      status: field.field_value ? "Detected" : "Not detected",
    },
  } as const;

  const active = palette[state] ?? palette.default;
  const examples: Record<string, string> = {
    MRP: "MRP ₹50.00 (inclusive of all taxes)",
    NET_QUANTITY: "Net Qty 500 g",
    MFG_DATE: "Mfg. 08/2026",
    COUNTRY_OF_ORIGIN: "Country of Origin: India",
    COMMON_NAME: "Potato chips",
    CONSUMER_CARE: "Customer care: 1800 000 000",
  };

  function toggle() {
    setOpen((current) => !current);
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-expanded={open}
      onClick={toggle}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          toggle();
        }
      }}
      className={cn(
        "group relative w-full overflow-hidden rounded-[1.35rem] border p-3.5 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40",
        active.shell
      )}
    >
      <div className={cn("absolute inset-y-0 left-0 w-1.5", active.accent)} />

      <div className="flex items-start justify-between gap-3 pl-3">
        <div className="flex min-w-0 items-start gap-3">
          <div className={cn("mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl", active.iconWrap)}>
            <Icon className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-[13px] font-semibold leading-tight text-card-foreground">{cfg.label}</p>
            <p className="rule-code mt-1 text-muted-foreground">{cfg.ruleRef}</p>
          </div>
        </div>

        <span className={cn("inline-flex items-center rounded-full px-2 py-1 text-[10px] font-medium uppercase tracking-[0.12em]", active.badge)}>
          {active.status}
        </span>
      </div>

      <div className="mt-4 pl-3">
        {field.field_value ? (
          <p className="break-words font-mono text-[15px] leading-6 text-card-foreground">{field.field_value}</p>
        ) : (
          <p className="text-sm leading-6 text-muted-foreground">
            {state === "verified_missing" || state === "not_detected_needs_review" ? cfg.hint : "No declaration was detected in the available label image."}
          </p>
        )}
      </div>

      {field.source_line && (
        <div className="mt-4 border-t border-ink-900/10 pl-3 pt-3 dark:border-paper-50/10">
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              setOpen((current) => !current);
            }}
            className="flex w-full items-center justify-between gap-3 text-left text-[11px] font-medium uppercase tracking-[0.12em] text-ink-700/70 dark:text-paper-100/70"
            aria-expanded={open}
          >
            <span>Evidence</span>
            <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", open && "rotate-180")} />
          </button>
          {open && <p className="mt-3 font-mono text-[11px] leading-5 text-ink-700/75 dark:text-paper-100/70">{field.source_line}</p>}
        </div>
      )}

      {open && (
        <div className="mt-4 flex items-start gap-2 rounded-xl border border-border bg-card/70 p-3 pl-3 text-[11px] leading-5 text-muted-foreground">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-700 dark:text-emerald-300" />
          <span>
            <strong className="font-medium text-ink-950 dark:text-paper-50">Why it matters:</strong> {cfg.hint} <strong className="font-medium text-ink-950 dark:text-paper-50">Example:</strong> {examples[field.field_name] ?? "A clear declaration in the prescribed format."}
          </span>
        </div>
      )}
    </div>
  );
}
