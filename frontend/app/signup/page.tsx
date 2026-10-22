import { Suspense } from "react";
import { FileCheck2, ScanLine, ShieldCheck } from "lucide-react";
import { SignupForm } from "@/components/auth/signup-form";
import { ThemeToggle } from "@/components/layout/theme-toggle";

export default function SignupPage() {
  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[1.1fr_1fr]">
      <div className="relative hidden overflow-hidden bg-ink-950 p-14 lg:flex lg:flex-col lg:justify-between">
        <div className="pointer-events-none absolute inset-0 bg-brass-grid bg-[size:44px_44px] opacity-60 [mask-image:radial-gradient(ellipse_80%_60%_at_30%_20%,black,transparent)]" />
        <div className="relative z-10 flex items-center gap-3"><div className="flex h-10 w-10 items-center justify-center rounded-lg border border-brass-500/40 bg-brass-500/10"><ScanLine className="h-5 w-5 text-brass-400" /></div><span className="font-display text-lg font-semibold text-paper-50">Metrology Verify</span></div>
        <div className="relative z-10 max-w-md"><p className="eyebrow mb-4">A working register for the field</p><h1 className="font-display text-[2.6rem] leading-[1.08] text-paper-50">Make every label read like evidence.</h1><p className="mt-5 text-[15px] leading-relaxed text-paper-100/55">Create an account to keep your inspection workspace close at hand, from the first photo to the final report.</p><div className="mt-10 flex flex-col gap-4 text-sm text-paper-100/70"><span className="flex items-center gap-3"><FileCheck2 className="h-4 w-4 text-brass-400" /> Rule-aware label checks</span><span className="flex items-center gap-3"><ShieldCheck className="h-4 w-4 text-brass-400" /> Secure, authorized access</span></div></div>
        <p className="relative z-10 text-xs text-paper-100/30">For authorized enforcement personnel only.</p>
      </div>
      <main className="relative flex min-h-screen items-center justify-center bg-paper-50 px-6 py-12 transition-colors duration-300 dark:bg-night-surface sm:px-10">
        <div className="absolute right-5 top-5"><ThemeToggle /></div>
        <Suspense fallback={null}><SignupForm /></Suspense>
      </main>
    </div>
  );
}