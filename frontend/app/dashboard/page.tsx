"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Navbar } from "@/components/layout/navbar";
import { BadgeCheck, Camera, ScanLine, ShieldCheck, BookOpen, History, Trash2 } from "lucide-react";
import { UploadPanel } from "@/components/scanner/upload-panel";
import { ResultsPanel } from "@/components/scanner/results-panel";
import { scanLabel, ScanApiError } from "@/lib/api";
import type { ScanResponse } from "@/lib/types";
import { useAuth } from "@/context/auth-context";
import { RecentScans } from "@/components/scanner/recent-scans";
import { GuideModal } from "@/components/scanner/guide-modal";
import { Button } from "@/components/ui/button";

type ViewState = "idle" | "scanning" | "results";

export default function DashboardPage() {
  const { officer } = useAuth();
  const [view, setView] = useState<ViewState>("idle");
  const [scanStep, setScanStep] = useState(0);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recentScans, setRecentScans] = useState<ScanResponse[]>([]);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const stepTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem("metrology-recent-scans");
      const parsed = stored ? JSON.parse(stored) : [];
      setRecentScans(Array.isArray(parsed) ? parsed : []);
      setShowOnboarding(!window.localStorage.getItem("metrology-onboarding-seen"));
    } catch {
      setRecentScans([]);
    }
    return () => {
      if (stepTimer.current) clearInterval(stepTimer.current);
    };
  }, []);

  async function handleSubmit(file: File) {
    setError(null);
    setView("scanning");
    setScanStep(0);
    setPreviewUrl(URL.createObjectURL(file));

    stepTimer.current = setInterval(() => {
      setScanStep((s) => Math.min(s + 1, 3));
    }, 900);

    try {
      const scan = await scanLabel(file);
      setResult(scan);
      setView("results");
      setRecentScans((current) => {
        const next = [scan, ...current.filter((item) => item.id !== scan.id)].slice(0, 5);
        return next;
      });
      try {
        const stored = JSON.parse(window.localStorage.getItem("metrology-recent-scans") || "[]");
        const next = [scan, ...(Array.isArray(stored) ? stored : []).filter((item: ScanResponse) => item.id !== scan.id)].slice(0, 5);
        window.localStorage.setItem("metrology-recent-scans", JSON.stringify(next));
      } catch (storageError) {
        if (process.env.NODE_ENV === "development") {
          console.debug("[scan] could not persist recent scan", storageError);
        }
      }
    } catch (err) {
      const message =
        err instanceof ScanApiError ? err.message : "Something went wrong while scanning.";
      setError(message);
      setView("idle");
    } finally {
      if (stepTimer.current) clearInterval(stepTimer.current);
    }
  }

  function handleNewScan() {
    setResult(null);
    setError(null);
    setView("idle");
  }

  function dismissOnboarding() {
    window.localStorage.setItem("metrology-onboarding-seen", "1");
    setShowOnboarding(false);
  }

  function openRecentScan(scan: ScanResponse) {
    setResult(scan);
    setPreviewUrl(null);
    setView("results");
  }

  function clearRecentScans() {
    if (!window.confirm("Clear all saved scans from this device?")) return;
    window.localStorage.removeItem("metrology-recent-scans");
    setRecentScans([]);
  }

  return (
    <div className="min-h-screen bg-background transition-colors duration-300">
      <Navbar />
      <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-10">
        <section className="relative mb-8 overflow-hidden rounded-[2rem] border border-border bg-card px-6 py-8 shadow-hero sm:px-8 sm:py-10">
          <div className="pointer-events-none absolute inset-0 bg-inspection-grid bg-[size:26px_26px] opacity-30" />
          <div className="relative z-10 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl">
              <div className="mb-4 flex items-center gap-2 text-emerald-700 dark:text-emerald-300">
                <ScanLine className="h-4 w-4" />
                <p className="font-mono text-[11px] uppercase tracking-[0.2em]">Your inspection desk</p>
              </div>
              <h1 className="font-display text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">Read the label. Know the rule.</h1>
              <p className="mt-3 max-w-xl text-[15px] leading-7 text-ink-800/75 dark:text-paper-100/75">
                Capture a packet label to begin a new read, then review the extracted declarations in a calm inspection sheet.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-xs text-ink-800/80 dark:text-paper-100/80">
              <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card/80 px-3 py-2">
                <span className="h-2 w-2 rounded-full bg-emerald-600" />
                Scanner ready
              </span>
              <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card/80 px-3 py-2">
                <span className="h-2 w-2 rounded-full bg-saffron-500" />
                OCR connected
              </span>
            </div>
          </div>
        </section>

        <div className="mb-7 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="eyebrow mb-1">Inspection desk</p>
            <h2 className="font-display text-2xl font-semibold text-foreground">Capture a package label</h2>
            <p className="mt-1 max-w-xl text-sm text-ink-700/70 dark:text-paper-100/65">Upload a label photo, run the rule checks, and review a clear record of every declaration.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button type="button" variant="outline" size="sm" onClick={() => recentScans[0] && openRecentScan(recentScans[0])} disabled={!recentScans.length} className="border-ink-900/15 text-ink-900 dark:border-paper-50/20 dark:text-paper-50"><History className="h-3.5 w-3.5" /> View last scan</Button>
            <Button type="button" variant="outline" size="sm" onClick={clearRecentScans} disabled={!recentScans.length} className="border-ink-900/15 text-ink-900 dark:border-paper-50/20 dark:text-paper-50"><Trash2 className="h-3.5 w-3.5" /> Clear all</Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setShowGuide(true)} className="border-ink-900/15 text-ink-900 dark:border-paper-50/20 dark:text-paper-50"><BookOpen className="h-3.5 w-3.5" /> Guide</Button>
          </div>
        </div>

        {showOnboarding && view === "idle" && (
          <div className="relative mb-5 rounded-[1.3rem] border border-saffron-500/30 bg-saffron-50 px-5 py-4 text-sm text-ink-950 shadow-sm dark:border-saffron-500/30 dark:bg-saffron-500/10 dark:text-paper-50" role="status">
            <p className="font-medium">Start with a clear label photo.</p>
            <p className="mt-1 text-ink-700/75 dark:text-paper-100/65">We&apos;ll extract mandatory declarations and flag anything that needs attention.</p>
            <button type="button" onClick={dismissOnboarding} className="absolute right-4 top-3 text-xs font-medium text-emerald-700 underline-offset-4 hover:underline dark:text-emerald-300">Got it</button>
          </div>
        )}

        <AnimatePresence mode="wait">
          {view !== "results" ? (
            <motion.div key="upload" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="mx-auto max-w-4xl">
              <UploadPanel onSubmit={handleSubmit} isScanning={view === "scanning"} scanStep={scanStep} errorMessage={error} />
            </motion.div>
          ) : (
            result && (
              <motion.div key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <ResultsPanel scan={result} previewUrl={previewUrl} onNewScan={handleNewScan} />
              </motion.div>
            )
          )}
        </AnimatePresence>

        {view === "idle" && <RecentScans scans={recentScans} onOpen={openRecentScan} onClear={clearRecentScans} />}
      </main>
      <GuideModal open={showGuide} onClose={() => setShowGuide(false)} />
    </div>
  );
}
