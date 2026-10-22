"use client";

import Link from "next/link";
import { ArrowRight, BadgeCheck, Camera, FileCheck2, ScanLine, ShieldCheck, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { useAuth } from "@/context/auth-context";
import { ThemeToggle } from "@/components/layout/theme-toggle";

const steps = [
  ["01", "Capture the label", "Upload a packet photo or use your camera."],
  ["02", "Read the declaration", "OCR extracts MRP, date, pack size, and origin details."],
  ["03", "Check the rule", "The engine aligns the label against legal-metrology checks."],
  ["04", "Export the finding", "Share a clean, review-ready compliance record."],
];

const trustMarks = ["Rule 6 aware", "OCR-assisted", "Review-ready", "Camera-friendly"];

function HeroPreview() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96, y: 16 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.7, delay: 0.15 }}
      className="relative z-10 mx-auto w-full max-w-[500px]"
    >
      <div aria-hidden="true" className="pointer-events-none absolute -inset-8 rounded-[2.2rem] bg-emerald-500/10 blur-3xl" />
      <div className="relative overflow-hidden rounded-[2.1rem] border border-border bg-card p-4 shadow-hero">
        <div className="rounded-[1.5rem] border border-border bg-secondary p-4">
          <div className="flex items-center justify-between border-b border-ink-900/10 pb-4 dark:border-paper-50/10">
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-full border border-emerald-600/15 bg-emerald-50 text-emerald-700 dark:border-emerald-300/20 dark:bg-emerald-500/10 dark:text-emerald-300">
                <ScanLine className="h-3.5 w-3.5" />
              </span>
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-ink-700/70 dark:text-paper-100/60">Inspection</span>
            </div>
            <span className="inline-flex items-center gap-2 rounded-full border border-emerald-600/15 bg-emerald-50 px-2.5 py-1 text-[10px] font-medium text-emerald-700 dark:border-emerald-300/20 dark:bg-emerald-500/10 dark:text-emerald-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-600 dark:bg-emerald-300" />
              Ready
            </span>
          </div>

          <div className="mt-6 grid gap-3 md:grid-cols-[1.2fr_0.8fr]">
            <div className="rounded-[1.2rem] border border-border bg-card p-4">
              <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-ink-700/60 dark:text-paper-100/60">Common name</p>
              <p className="mt-2 font-display text-[1.6rem] leading-none text-ink-950 dark:text-paper-50">Potato chips</p>
              <div className="mt-4 border-t border-ink-900/10 pt-3 dark:border-paper-50/10">
                <div className="flex items-end justify-between">
                  <div>
                    <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-ink-700/60 dark:text-paper-100/60">MRP</p>
                    <p className="mt-2 text-[1.55rem] font-semibold tracking-tight text-ink-950 dark:text-paper-50">₹50.00</p>
                  </div>
                  <div className="rounded-full border border-emerald-500/20 bg-emerald-50 px-2 py-1 text-[10px] font-medium text-emerald-700 dark:border-emerald-300/20 dark:bg-emerald-500/10 dark:text-emerald-300">
                    Verified
                  </div>
                </div>
              </div>
            </div>
            <div className="space-y-3">
              <div className="rounded-[1.2rem] border border-saffron-500/20 bg-saffron-50 p-4 dark:border-saffron-500/20 dark:bg-saffron-500/10">
                <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-saffron-600 dark:text-saffron-300">Net qty</p>
                <p className="mt-2 text-[1.35rem] font-semibold text-ink-950 dark:text-paper-50">55 g</p>
              </div>
              <div className="rounded-[1.2rem] border border-border bg-card p-4">
                <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-ink-700/60 dark:text-paper-100/60">Country</p>
                <p className="mt-2 text-base font-medium text-ink-950 dark:text-paper-50">India</p>
              </div>
            </div>
          </div>

          <div className="mt-5 rounded-[1.2rem] border border-border bg-card p-3">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="h-px flex-1 bg-ink-900/10 dark:bg-paper-50/10" />
              <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-ink-700/60 dark:text-paper-100/60">OCR bands</span>
              <div className="h-px flex-1 bg-ink-900/10 dark:bg-paper-50/10" />
            </div>
            <div className="space-y-2">
              <div className="h-2 rounded-full bg-emerald-500/25">
                <div className="h-full w-[82%] rounded-full bg-emerald-600" />
              </div>
              <div className="h-2 rounded-full bg-saffron-500/25">
                <div className="h-full w-[58%] rounded-full bg-saffron-500" />
              </div>
              <div className="h-2 rounded-full bg-ink-900/10 dark:bg-paper-50/10">
                <div className="h-full w-[70%] rounded-full bg-ink-900/50 dark:bg-paper-50/60" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function HomePage() {
  const { user } = useAuth();
  const startHref = user ? "/dashboard" : "/login?next=/dashboard";

  return (
    <main className="min-h-screen overflow-hidden bg-background text-foreground">
      <header className="relative z-50 mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8">
        <Link href="/" className="flex items-center gap-3" aria-label="Metrology Verify home">
          <span className="brand-mark">
            <ScanLine className="h-[18px] w-[18px] text-emerald-700 dark:text-emerald-300" strokeWidth={2.2} />
          </span>
          <span>
            <strong className="font-display text-base text-ink-950 dark:text-paper-50">Metrology Verify</strong>
            <span className="mt-0.5 block font-mono text-[9px] uppercase tracking-[0.18em] text-ink-700/60 dark:text-paper-100/60">Label intelligence</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-6 md:flex" aria-label="Main navigation">
          <Link href="/#how-it-works" className="text-sm font-medium text-ink-700 transition hover:text-emerald-700 dark:text-paper-100/70 dark:hover:text-emerald-300">How it works</Link>
          <Link href={user ? "/dashboard" : "/login?next=/dashboard"} className="text-sm font-medium text-ink-700 transition hover:text-emerald-700 dark:text-paper-100/70 dark:hover:text-emerald-300">{user ? "Dashboard" : "My scans"}</Link>
        </nav>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Link href={startHref} className="hidden text-sm font-medium text-ink-700 hover:text-emerald-700 sm:inline-flex dark:text-paper-100/70 dark:hover:text-emerald-300">{user ? "Open desk" : "Sign in"}</Link>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl items-center gap-12 px-5 pb-16 pt-8 sm:px-8 sm:pt-14 lg:grid-cols-[1.08fr_0.92fr] lg:pb-20">
        <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="relative z-10">
          <p className="eyebrow mb-5 flex items-center gap-2"><Sparkles className="h-3.5 w-3.5" /> Legal metrology, made legible</p>
          <h1 className="max-w-xl font-display text-5xl font-semibold leading-[0.95] tracking-[-0.04em] sm:text-6xl">
            Know what the label says.<br />
            <span className="text-emerald-700 dark:text-emerald-300">Know what it means.</span>
          </h1>
          <p className="mt-6 max-w-xl text-base leading-8 text-ink-700/80 dark:text-paper-100/70">
            Turn a packaged-goods label photo into a clear compliance read for MRP, net quantity, origin, dates, manufacturer details, and any declaration that needs review.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link href={startHref} className="inline-flex h-12 items-center gap-2 rounded-xl bg-primary px-6 text-sm font-semibold text-primary-foreground shadow-card transition-all duration-200 hover:-translate-y-0.5 hover:bg-primary/90 hover:shadow-card-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40">
              Scan a label
              <ArrowRight className="h-4 w-4" />
            </Link>
            <a href="#how-it-works" className="inline-flex h-12 items-center rounded-xl border border-ink-900/10 bg-surface/70 px-5 text-sm font-medium text-ink-900 transition-all duration-200 hover:-translate-y-0.5 hover:bg-ink-900/5 dark:border-paper-50/15 dark:bg-paper-50/5 dark:text-paper-50 dark:hover:bg-paper-50/10">
              See how it works
            </a>
          </div>

          <div className="mt-8 flex flex-wrap gap-x-5 gap-y-3 text-xs text-ink-700/70 dark:text-paper-100/70">
            {trustMarks.map((label) => (
              <span key={label} className="flex items-center gap-2 border-b border-ink-900/10 pb-1 dark:border-paper-50/10">
                <BadgeCheck className="h-3.5 w-3.5 text-emerald-700 dark:text-emerald-300" />
                {label}
              </span>
            ))}
          </div>
        </motion.div>

        <HeroPreview />
      </section>

      <section id="how-it-works" className="border-y border-border bg-card/70 py-20">
        <div className="mx-auto max-w-7xl px-5 sm:px-8">
          <p className="eyebrow">A clearer path to certainty</p>
          <h2 className="mt-3 max-w-xl font-display text-3xl font-semibold tracking-tight sm:text-4xl">From packet to proof in four deliberate steps.</h2>

          <div className="mt-10 grid gap-4 lg:grid-cols-4">
            {steps.map(([number, title, description], index) => (
              <motion.div
                key={number}
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-40px" }}
                transition={{ duration: 0.45, delay: index * 0.08 }}
                className="rounded-[1.5rem] border border-border bg-card p-6 shadow-card"
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="font-mono text-xs uppercase tracking-[0.2em] text-emerald-700 dark:text-emerald-300">{number}</span>
                  <span className="h-px flex-1 bg-ink-900/10 dark:bg-paper-50/10" />
                </div>
                <h3 className="mt-8 font-display text-2xl font-semibold text-ink-950 dark:text-paper-50">{title}</h3>
                <p className="mt-3 text-sm leading-7 text-ink-700/75 dark:text-paper-100/65">{description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-8 px-5 py-20 sm:px-8">
        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-[1.75rem] border border-border bg-card p-7 shadow-card">
            <p className="eyebrow">Evidence, not guesswork</p>
            <h2 className="mt-4 font-display text-3xl font-semibold tracking-tight sm:text-4xl">Label facts that stay traceable.</h2>
            <p className="mt-4 text-base leading-8 text-ink-700/75 dark:text-paper-100/70">
              Every declaration keeps its context — MRP, net quantity, origin, dates, manufacturer details, and any missing or review-only signals are surfaced with the original label read.
            </p>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <div className="rounded-[1.5rem] border border-border bg-card p-6 shadow-card">
              <ShieldCheck className="h-5 w-5 text-emerald-700 dark:text-emerald-300" />
              <h3 className="mt-5 font-display text-2xl font-semibold">Rule-aware</h3>
              <p className="mt-3 text-sm leading-7 text-ink-700/75 dark:text-paper-100/65">Explicit declaration context keeps every check tied to the relevant Legal Metrology requirement.</p>
            </div>
            <div className="rounded-[1.5rem] border border-border bg-card p-6 shadow-card">
              <Camera className="h-5 w-5 text-saffron-600 dark:text-saffron-300" />
              <h3 className="mt-5 font-display text-2xl font-semibold">Camera-friendly</h3>
              <p className="mt-3 text-sm leading-7 text-ink-700/75 dark:text-paper-100/65">Built for real packaging photos, less-than-perfect angles, and the tiny print that matters in enforcement checks.</p>
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-[1.75rem] border border-border bg-card p-7 shadow-card">
            <p className="eyebrow">Built for the small print</p>
            <h2 className="mt-4 font-display text-3xl font-semibold tracking-tight sm:text-4xl">A calmer way to read a crowded package.</h2>
            <ul className="mt-6 space-y-4 text-sm leading-7 text-ink-700/75 dark:text-paper-100/65">
              <li className="flex gap-3"><span className="mt-1 h-2 w-2 rounded-full bg-emerald-600" />MRP and net quantity detection stay separate from cosmetic label text.</li>
              <li className="flex gap-3"><span className="mt-1 h-2 w-2 rounded-full bg-saffron-500" />Review states are called out clearly without sensationalizing the issue.</li>
              <li className="flex gap-3"><span className="mt-1 h-2 w-2 rounded-full bg-ink-900/70 dark:bg-paper-50/70" />Field-level evidence keeps the final read grounded in what was actually extracted.</li>
            </ul>
          </div>

          <div className="rounded-[1.75rem] border border-border bg-accent p-7 shadow-card">
            <p className="eyebrow text-emerald-700 dark:text-emerald-300">Inspection signal</p>
            <div className="mt-5 space-y-4">
              <div className="flex items-center justify-between rounded-2xl border border-border bg-card/70 px-4 py-3">
                <span className="text-sm font-medium text-ink-950 dark:text-paper-50">MRP</span>
                <span className="font-mono text-sm text-emerald-700 dark:text-emerald-300">₹50.00</span>
              </div>
              <div className="flex items-center justify-between rounded-2xl border border-border bg-card/70 px-4 py-3">
                <span className="text-sm font-medium text-ink-950 dark:text-paper-50">Net quantity</span>
                <span className="font-mono text-sm text-saffron-600 dark:text-saffron-300">55 g</span>
              </div>
              <div className="flex items-center justify-between rounded-2xl border border-border bg-card/70 px-4 py-3">
                <span className="text-sm font-medium text-ink-950 dark:text-paper-50">Country of origin</span>
                <span className="font-mono text-sm text-ink-700/80 dark:text-paper-100/75">India</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-ink-900/10 px-5 py-8 dark:border-paper-50/10">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 text-center text-xs text-ink-700/65 sm:flex-row sm:text-left dark:text-paper-100/60">
          <div>
            <p className="font-display text-base text-ink-950 dark:text-paper-50">Metrology Verify</p>
            <p className="mt-1">A clearer read on packaged-commodity compliance.</p>
          </div>
          <div className="flex items-center gap-4">
            <span>Privacy</span>
            <span>Legal</span>
            <span>Status</span>
          </div>
        </div>
      </footer>
    </main>
  );
}
