"use client";

import { motion } from "framer-motion";
import { AlertTriangle, ShieldCheck, ChevronDown } from "lucide-react";
import { useState } from "react";
import type { ViolationDetail } from "@/lib/types";

export function ViolationList({ violations }: { violations: ViolationDetail[] }) {
  if (violations.length === 0) {
    return (
      <div className="flex items-center gap-3 rounded-[1.2rem] border border-success/30 bg-success-surface px-5 py-4">
        <ShieldCheck className="h-[18px] w-[18px] shrink-0 text-success" />
        <p className="text-sm text-accent-foreground">
          No violations detected — every mandatory declaration was found on the label.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      {violations.map((v, i) => (
        <ViolationItem key={v.id ?? v.rule_code} violation={v} index={i} />
      ))}
    </div>
  );
}

function ViolationItem({ violation: v, index: i }: { violation: ViolationDetail; index: number }) {
  const [open, setOpen] = useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: i * 0.05 }}
      className="relative overflow-hidden rounded-[1.2rem] border border-warning/30 border-l-4 bg-warning-surface shadow-sm transition-all duration-200 hover:shadow-card-hover"
    >
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        aria-expanded={open}
        className="flex w-full items-start gap-3 px-5 py-4 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600/40 focus-visible:ring-inset"
      >
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
        <span className="min-w-0 flex-1">
          <span className="rule-code block text-warning">{v.rule_code}</span>
          <span className="mt-1 block text-[13px] leading-relaxed text-secondary-foreground">{v.description}</span>
        </span>
        <ChevronDown className={`mt-0.5 h-4 w-4 shrink-0 text-warning transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="border-t border-warning/30 px-5 py-4 text-xs leading-5 text-muted-foreground">
          <p>
            <strong className="text-ink-950 dark:text-paper-50">Rule context:</strong> This finding maps to {v.rule_code.replaceAll("_", " ")} and indicates that the declaration may be missing or not clearly legible on the package.
          </p>
          <p className="mt-2">
            <strong className="text-ink-950 dark:text-paper-50">What to fix:</strong> Re-check the declaration on the physical package and ensure the wording is visible, legible, and in the required format before finalizing the read.
          </p>
        </div>
      )}
    </motion.div>
  );
}
