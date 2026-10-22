import { Suspense } from "react";
import { ScanLine, ShieldCheck, FileCheck2 } from "lucide-react";
import { LoginForm } from "@/components/auth/login-form";
import { ThemeToggle } from "@/components/layout/theme-toggle";

export default function LoginPage() {
  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[1.1fr_1fr]">
      {/* Branded panel */}
      <div className="relative hidden overflow-hidden bg-ink-950 lg:flex lg:flex-col lg:justify-between lg:p-14">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 bg-brass-grid bg-[size:44px_44px] opacity-60 [mask-image:radial-gradient(ellipse_80%_60%_at_30%_20%,black,transparent)]"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 bg-ink-radial"
        />

        {/* Brand */}
        <div className="relative z-10 flex items-center gap-3 text-white">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-white/30 bg-white/5 text-emerald-300 shadow-[0_0_28px_rgba(110,231,183,0.12)]">
            <ScanLine
              className="h-5 w-5 text-emerald-300"
              aria-hidden="true"
            />
          </div>

          <div className="leading-none">
            <p className="font-display text-lg font-semibold tracking-tight text-white">
              Metrology Verify
            </p>
            <p className="mt-1 text-[10px] font-medium uppercase tracking-[0.22em] text-emerald-200/90">
              Label Intelligence
            </p>
          </div>
        </div>

        <div className="relative z-10 max-w-md">
          <p className="eyebrow mb-4 text-emerald-200/70">
            Government of India · Consumer Affairs
          </p>

          <h2 className="font-display text-[2.6rem] leading-[1.08] tracking-tight text-paper-50">
            Every label,
            <br />
            held to the letter
            <br />
            of the law.
          </h2>

          <p className="mt-5 text-[15px] leading-relaxed text-paper-100/70">
            Point a camera at a package. In seconds, get a rule-by-rule
            reading against the Legal Metrology (Packaged Commodities) Rules,
            2011 — MRP, net quantity, origin, dates, and manufacturer
            declarations, cross-checked automatically.
          </p>

          <div className="mt-10 flex flex-col gap-4">
            <div className="flex items-center gap-3 text-sm text-paper-100/80">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-white/15 bg-white/[0.06]">
                <FileCheck2
                  className="h-3.5 w-3.5 text-emerald-300"
                  aria-hidden="true"
                />
              </div>
              Rule-6 &amp; Rule-18 declarations checked automatically
            </div>

            <div className="flex items-center gap-3 text-sm text-paper-100/80">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-white/15 bg-white/[0.06]">
                <ShieldCheck
                  className="h-3.5 w-3.5 text-emerald-300"
                  aria-hidden="true"
                />
              </div>
              Exportable compliance reports for enforcement records
            </div>
          </div>
        </div>

        <p className="relative z-10 text-xs text-paper-100/45">
          For authorized enforcement personnel only. Unauthorized access is
          prohibited.
        </p>
      </div>

      {/* Form panel */}
      <div className="relative flex items-center justify-center bg-paper-50 p-6 transition-colors duration-300 sm:p-10 dark:bg-night-surface">
        <div className="absolute right-5 top-5 z-20">
          <ThemeToggle />
        </div>

        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 opacity-[0.035] [background-image:linear-gradient(#0A0F1A_1px,transparent_1px),linear-gradient(90deg,#0A0F1A_1px,transparent_1px)] [background-size:32px_32px] dark:opacity-[0.06]"
        />

        {/* Mobile-only brand */}
        <div className="relative z-10 mb-10 flex w-full max-w-sm items-center gap-3 lg:hidden">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-700/20 bg-emerald-700/10 text-emerald-700 dark:border-emerald-300/25 dark:bg-emerald-300/10 dark:text-emerald-300">
            <ScanLine className="h-5 w-5" aria-hidden="true" />
          </div>

          <div className="leading-none">
            <p className="font-display text-lg font-semibold tracking-tight text-ink-900 dark:text-paper-50">
              Metrology Verify
            </p>
            <p className="mt-1 text-[10px] font-medium uppercase tracking-[0.22em] text-emerald-700/75 dark:text-emerald-300/80">
              Label Intelligence
            </p>
          </div>
        </div>

        <Suspense fallback={null}>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}