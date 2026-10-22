"use client";

import { useState, type FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mail,
  Lock,
  AlertCircle,
  Loader2,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M23.49 12.27c0-.79-.07-1.54-.2-2.27H12v4.3h6.47a5.54 5.54 0 0 1-2.4 3.63v3h3.88c2.27-2.09 3.54-5.17 3.54-8.66Z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.24 0 5.95-1.07 7.93-2.9l-3.88-3c-1.08.72-2.46 1.15-4.05 1.15-3.11 0-5.75-2.1-6.69-4.92H1.3v3.09A12 12 0 0 0 12 24Z"
      />
      <path
        fill="#FBBC05"
        d="M5.31 14.33A7.2 7.2 0 0 1 4.93 12c0-.81.14-1.6.38-2.33V6.58H1.3A12 12 0 0 0 0 12c0 1.94.46 3.77 1.3 5.42l4.01-3.09Z"
      />
      <path
        fill="#EA4335"
        d="M12 4.75c1.76 0 3.34.61 4.58 1.8l3.44-3.44C17.94 1.19 15.24 0 12 0 7.31 0 3.26 2.69 1.3 6.58l4.01 3.09C6.25 6.85 8.89 4.75 12 4.75Z"
      />
    </svg>
  );
}

export function LoginForm() {
  const { signInWithPassword, signInWithGoogle } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setNotice(null);

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError("Enter a valid email address.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setSubmitting(true);

    const result = await signInWithPassword(email, password);

    setSubmitting(false);

    if (!result.ok) {
      setError(result.error ?? "Something went wrong. Please try again.");
      return;
    }

    router.push(searchParams.get("next") || "/dashboard");
  }

  async function handleGoogle() {
    setError(null);
    setNotice(null);
    setGoogleLoading(true);

    const result = await signInWithGoogle();

    if (!result.ok) {
      setGoogleLoading(false);
      setError(
        result.error ??
          "Google sign-in could not be started. Please try again."
      );
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="w-full max-w-sm"
    >
      <div className="mb-8">
        <p className="eyebrow mb-3 text-ink-600">Field Officer Access</p>

        <h1 className="font-display text-3xl font-semibold tracking-tight text-ink-900 dark:text-paper-50">
          Sign in to the register
        </h1>

        <p className="mt-2 text-sm text-ink-700/70 dark:text-paper-100/70">
          Verify packaged-commodity labels against the Legal Metrology
          (Packaged Commodities) Rules, 2011.
        </p>
      </div>

      <Button
        type="button"
        variant="outline"
        size="lg"
        disabled={googleLoading}
        onClick={handleGoogle}
        className="mb-5 w-full border-border bg-card text-card-foreground hover:bg-accent"
      >
        {googleLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <GoogleIcon />
        )}
        Continue with Google
      </Button>

      {/* Clean OR divider — no empty logo square here */}
      <div className="mb-5 flex items-center gap-3">
        <div className="h-px flex-1 bg-ink-700/10 dark:bg-paper-50/15" />
        <span className="text-xs uppercase tracking-wide text-ink-700/40 dark:text-paper-100/45">
          or
        </span>
        <div className="h-px flex-1 bg-ink-700/10 dark:bg-paper-50/15" />
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <div className="space-y-5">
          <div>
            <Label
              htmlFor="email"
              className="text-ink-700 dark:text-paper-100/80"
            >
              Email
            </Label>

            <div className="relative">
              <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-600/50" />

              <Input
                id="email"
                type="email"
                placeholder="officer@dept.gov.in"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
                className="border-ink-700/15 bg-ink-900/[0.03] pl-10 text-ink-900 placeholder:text-ink-700/35 focus-visible:border-brass-600 dark:border-paper-50/15 dark:bg-paper-50/[0.06] dark:text-paper-50 dark:placeholder:text-paper-100/35"
              />
            </div>
          </div>

          <div>
            <Label
              htmlFor="password"
              className="text-ink-700 dark:text-paper-100/80"
            >
              Password
            </Label>

            <div className="relative">
              <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-600/50" />

              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                minLength={6}
                required
                className="border-ink-700/15 bg-ink-900/[0.03] pl-10 text-ink-900 placeholder:text-ink-700/35 focus-visible:border-brass-600 dark:border-paper-50/15 dark:bg-paper-50/[0.06] dark:text-paper-50 dark:placeholder:text-paper-100/35"
              />
            </div>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="flex items-start gap-2 rounded-lg border border-fail/30 bg-fail/[0.06] px-3.5 py-2.5 text-[13px] text-fail"
              >
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>{error}</span>
              </motion.div>
            )}

            {notice && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="flex items-start gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/[0.06] px-3.5 py-2.5 text-[13px] text-emerald-700 dark:text-emerald-300"
              >
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>{notice}</span>
              </motion.div>
            )}
          </AnimatePresence>

          <Button type="submit" size="lg" disabled={submitting} className="w-full">
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Signing in…
              </>
            ) : (
              <>
                Sign in
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </Button>
        </div>
      </form>

      <div className="mt-6 flex items-center justify-between text-sm">
        <Link
          href="#"
          className="text-teal-700 underline-offset-4 hover:underline dark:text-teal-300"
        >
          Forgot password?
        </Link>

        <Link
          href="/signup"
          className="font-medium text-ink-900 underline-offset-4 hover:underline dark:text-paper-50"
        >
          Create an account
        </Link>
      </div>
    </motion.div>
  );
}