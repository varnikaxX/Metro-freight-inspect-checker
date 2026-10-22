"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Loader2, Mail, Lock, UserRound, AlertCircle, CheckCircle2 } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { useAuth } from "@/context/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function SignupForm() {
  const { signUpWithPassword } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError("Enter a valid email address.");
      return;
    }
    if (password.length < 6) {
      setError("Use at least 6 characters for your password.");
      return;
    }
    setSubmitting(true);
    const result = await signUpWithPassword(email, password, name);
    setSubmitting(false);
    if (!result.ok) {
      setError(result.error ?? "Could not create your account.");
      return;
    }
    if (result.needsEmailConfirm) {
      setNotice("Check your inbox to confirm your email, then sign in.");
      return;
    }
    router.push("/dashboard");
  }

  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease: "easeOut" }} className="w-full max-w-sm">
      <div className="mb-8">
        <p className="eyebrow mb-3">Field Officer Access</p>
        <h1 className="font-display text-3xl font-semibold tracking-tight text-ink-900 dark:text-paper-50">Create your account</h1>
        <p className="mt-2 text-sm text-ink-700/70 dark:text-paper-100/70">Create a secure account to review label compliance scans.</p>
      </div>
      <form onSubmit={handleSubmit} noValidate className="space-y-5">
        <div><Label htmlFor="name">Name (optional)</Label><div className="relative"><UserRound className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-600/50" /><Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Asha Mehta" className="pl-10 bg-ink-900/[0.03] text-ink-900 dark:bg-paper-50/[0.06] dark:text-paper-50" /></div></div>
        <div><Label htmlFor="signup-email">Email</Label><div className="relative"><Mail className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-600/50" /><Input id="signup-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="officer@dept.gov.in" className="pl-10 bg-ink-900/[0.03] text-ink-900 dark:bg-paper-50/[0.06] dark:text-paper-50" /></div></div>
        <div><Label htmlFor="signup-password">Password</Label><div className="relative"><Lock className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-600/50" /><Input id="signup-password" type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 6 characters" className="pl-10 bg-ink-900/[0.03] text-ink-900 dark:bg-paper-50/[0.06] dark:text-paper-50" /></div></div>
        <AnimatePresence>
          {error && <motion.p initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} role="alert" className="flex items-start gap-2 rounded-lg border border-fail/30 bg-fail/[0.06] px-3 py-2 text-sm text-fail"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />{error}</motion.p>}
          {notice && <motion.p initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} role="status" className="flex items-start gap-2 rounded-lg border border-teal-500/25 bg-teal-500/10 px-3 py-2 text-sm text-teal-700 dark:text-teal-300"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />{notice}</motion.p>}
        </AnimatePresence>
        <Button size="lg" type="submit" disabled={submitting} className="w-full">{submitting ? <><Loader2 className="h-4 w-4 animate-spin" /> Creating account…</> : <>Create account <ArrowRight className="h-4 w-4" /></>}</Button>
      </form>
      <p className="mt-6 text-center text-sm text-ink-700/70 dark:text-paper-100/70">Already registered? <Link href="/login" className="font-medium text-teal-700 hover:underline dark:text-teal-300">Sign in</Link></p>
    </motion.div>
  );
}