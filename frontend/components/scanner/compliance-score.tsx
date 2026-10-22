"use client";

import { motion } from "framer-motion";
import { InfoTooltip } from "@/components/ui/info-tooltip";

export function ComplianceScore({
  present,
  total,
}: {
  present: number;
  total: number;
}) {
  const score = total > 0 ? Math.round((present / total) * 100) : 0;

  const isHigh = score >= 80;
  const isMedium = score >= 50;

  const scoreTextClass = isHigh
    ? "text-emerald-700 dark:text-emerald-300"
    : isMedium
      ? "text-amber-800 dark:text-amber-300"
      : "text-red-700 dark:text-red-300";

  const fillClass = isHigh
    ? "bg-emerald-600 dark:bg-emerald-400"
    : isMedium
      ? "bg-amber-500 dark:bg-amber-400"
      : "bg-red-600 dark:bg-red-400";

  const label = isHigh
    ? "Most declarations detected"
    : isMedium
      ? "Some declarations need review"
      : "Several declarations need review";

  return (
    <div className="min-w-[180px] rounded-xl border border-border bg-card p-4 text-card-foreground shadow-sm">
      <div className="flex items-end justify-between gap-3">
        <div>
          <p className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Verification coverage
            <InfoTooltip label="About verification coverage">
              This is the percentage of expected declarations detected by OCR.
              It is not a legal compliance score.
            </InfoTooltip>
          </p>

          <p className={`mt-1 font-display text-2xl font-semibold ${scoreTextClass}`}>
            {score}%
          </p>
        </div>

        <span className="font-mono text-xs text-muted-foreground">
          {present}/{total}
        </span>
      </div>

      <div
        className="mt-3 h-2.5 overflow-hidden rounded-full border border-black/5 bg-stone-300/80 p-[2px] dark:border-white/10 dark:bg-white/10"
        aria-label={`Verification coverage: ${score}%`}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={score}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className={`h-full rounded-full ${fillClass}`}
        />
      </div>

      <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
        {label}
      </p>
    </div>
  );
}