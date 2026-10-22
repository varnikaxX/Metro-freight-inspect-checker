"use client";

import { motion } from "framer-motion";
import { ScanLine } from "lucide-react";

const STEPS = [
  "Reading label geometry…",
  "Running OCR extraction…",
  "Checking Rule 6 declarations…",
  "Cross-referencing violations…",
];

export function ScanningOverlay({ step = 0 }: { step?: number }) {
  const activeStep = STEPS[Math.min(step, STEPS.length - 1)];

  return (
    <div
      className="absolute inset-0 z-20 overflow-hidden rounded-2xl"
      aria-live="polite"
      aria-busy="true"
    >
      {/* Theme-aware overlay surface */}
      <div className="pointer-events-none absolute inset-0 bg-paper-50/88 backdrop-blur-[1px] dark:bg-ink-950/70" />

      {/* Theme-aware scanner grid */}
      <div className="pointer-events-none absolute inset-0 bg-brass-grid bg-[size:28px_28px] opacity-[0.14] dark:opacity-20" />

      {/* Moving scanner / laser line */}
      <motion.div
        aria-hidden="true"
        className="pointer-events-none absolute left-0 right-0 h-[2px]"
        style={{
          background:
            "linear-gradient(90deg, transparent, rgba(24, 125, 91, 0.92), transparent)",
          boxShadow: "0 0 16px 2px rgba(24, 125, 91, 0.38)",
        }}
        animate={{ top: ["4%", "96%", "4%"] }}
        transition={{
          duration: 2.4,
          ease: "easeInOut",
          repeat: Infinity,
        }}
      />

      {/* Current scan status */}
      <div className="absolute inset-x-0 bottom-0 z-10 flex flex-col items-center gap-3 p-6">
        <div className="flex items-center gap-2 rounded-full border border-emerald-700/25 bg-paper-50/95 px-4 py-2 shadow-sm dark:border-emerald-300/30 dark:bg-ink-950/85">
          <ScanLine
            className="h-3.5 w-3.5 animate-pulse text-emerald-700 dark:text-emerald-300"
            aria-hidden="true"
          />

          <span className="font-mono text-[11px] font-medium uppercase tracking-widest text-ink-900 dark:text-paper-50">
            {activeStep}
          </span>
        </div>
      </div>

      {/* Scanner corner brackets */}
      {[
        "top-3 left-3 border-t-2 border-l-2",
        "top-3 right-3 border-t-2 border-r-2",
        "bottom-3 left-3 border-b-2 border-l-2",
        "bottom-3 right-3 border-b-2 border-r-2",
      ].map((pos, index) => (
        <div
          key={index}
          aria-hidden="true"
          className={`pointer-events-none absolute h-6 w-6 rounded-[3px] border-emerald-700/75 dark:border-emerald-300/75 ${pos}`}
        />
      ))}
    </div>
  );
}