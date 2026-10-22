"use client";

import { Check, X, AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { ComplianceVerdict } from "@/lib/types";

const VERDICT_CONFIG: Record<
  ComplianceVerdict,
  { ring: string; glow: string; icon: typeof Check; label: string; sub: string }
> = {
  PASS: {
    ring: "border-teal-600 text-teal-700",
    glow: "shadow-[0_0_60px_-10px_rgba(30,153,115,0.55)]",
    icon: Check,
    label: "Compliant",
    sub: "All mandatory declarations present",
  },
  VIOLATIONS: {
    ring: "border-coral-500 text-coral-600",
    glow: "shadow-[0_0_60px_-10px_rgba(214,52,71,0.55)]",
    icon: X,
    label: "Violations Detected",
    sub: "A declaration was verified missing",
  },
  MANUAL_REVIEW: {
    ring: "border-review text-review-fg",
    glow: "shadow-[0_0_60px_-10px_rgba(232,163,61,0.55)]",
    icon: AlertTriangle,
    label: "Manual Review Required",
    sub: "Label could not be reliably read",
  },
};

export function ComplianceSeal({ verdict }: { verdict: ComplianceVerdict }) {
  const cfg = VERDICT_CONFIG[verdict];
  const Icon = cfg.icon;

  return (
    <div className="flex items-center gap-5">
      <motion.div
        initial={{ scale: 0.7, opacity: 0, rotate: -8 }}
        animate={{ scale: 1, opacity: 1, rotate: 0 }}
        transition={{ type: "spring", stiffness: 180, damping: 14 }}
        className="relative shrink-0"
      >
        <div
          className={cn(
            "absolute inset-0 rounded-full border-2 border-dashed opacity-40",
            cfg.ring
          )}
          style={{ transform: "scale(1.18)" }}
        />
        <div
          className={cn(
            "relative flex h-24 w-24 items-center justify-center rounded-full border-2 bg-surface backdrop-blur dark:bg-night",
            cfg.ring,
            cfg.glow
          )}
        >
          <Icon className="h-9 w-9" strokeWidth={2.25} />
        </div>
      </motion.div>

      <div>
        <p className="eyebrow">Overall Result</p>
        <p className={cn("font-display text-2xl font-semibold", cfg.ring.split(" ")[1])}>
          {cfg.label}
        </p>
        <p className="mt-0.5 text-sm text-ink-700/65 dark:text-paper-100/65">{cfg.sub}</p>
      </div>
    </div>
  );
}
