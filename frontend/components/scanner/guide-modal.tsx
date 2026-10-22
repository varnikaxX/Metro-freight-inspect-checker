"use client";

import { X, Lightbulb, Upload, ScanSearch, ListChecks, Download } from "lucide-react";
import { Button } from "@/components/ui/button";

const steps = [
  [Upload, "Upload", "Choose a clear label photo or capture one with your camera."],
  [ScanSearch, "Scan", "Run OCR and rule checks against the packaged-commodity rules."],
  [ListChecks, "Review", "Open each field or finding to understand what it means."],
  [Download, "Export", "Download a report or JSON record for your inspection notes."],
] as const;

export function GuideModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/60 px-5 py-8 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="guide-title">
      <div className="w-full max-w-lg rounded-2xl border border-ink-900/10 bg-surface p-6 shadow-hero dark:border-paper-50/10 dark:bg-night-surface sm:p-8">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="eyebrow">Field guide</p>
            <h2 id="guide-title" className="mt-2 font-display text-2xl font-semibold text-ink-900 dark:text-paper-50">From photo to finding</h2>
          </div>
          <button type="button" onClick={onClose} aria-label="Close guide" className="rounded-full p-2 text-ink-700/60 hover:bg-ink-900/5 dark:text-paper-100/60 dark:hover:bg-paper-50/10"><X className="h-4 w-4" /></button>
        </div>
        <div className="mt-7 grid gap-4 sm:grid-cols-2">
          {steps.map(([Icon, title, description], index) => (
            <div key={title} className="rounded-xl border border-ink-900/10 bg-canvas/60 p-4 dark:border-paper-50/10 dark:bg-paper-50/[0.04]">
              <div className="flex items-center gap-3"><span className="font-mono text-xs text-brass-600 dark:text-brass-300">0{index + 1}</span><Icon className="h-4 w-4 text-teal-600" /><span className="font-medium text-ink-900 dark:text-paper-50">{title}</span></div>
              <p className="mt-3 text-sm leading-5 text-ink-700/70 dark:text-paper-100/65">{description}</p>
            </div>
          ))}
        </div>
        <div className="mt-5 flex items-start gap-3 rounded-xl border border-brass-500/25 bg-brass-500/10 p-4 text-sm text-ink-700 dark:text-paper-100"><Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-brass-600 dark:text-brass-300" /><span>Tips: use even lighting, keep the package flat, and fill the frame with the printed declarations.</span></div>
        <Button type="button" onClick={onClose} className="mt-6 w-full">Back to scan</Button>
      </div>
    </div>
  );
}