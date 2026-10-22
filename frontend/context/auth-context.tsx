"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { User } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabase/client";
import { deleteAccount as deleteAccountRequest } from "@/lib/api";

export interface OfficerSession {
  badgeId: string;
  name: string;
  jurisdiction: string;
}

interface AuthResult {
  ok: boolean;
  error?: string;
  needsEmailConfirm?: boolean;
}

interface AuthContextValue {
  officer: OfficerSession | null;
  user: User | null;
  isLoading: boolean;
  signInWithPassword: (email: string, password: string) => Promise<AuthResult>;
  signUpWithPassword: (email: string, password: string, name?: string) => Promise<AuthResult>;
  signInWithGoogle: () => Promise<AuthResult>;
  logout: () => Promise<void>;
  deleteAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function toOfficerSession(user: User | null): OfficerSession | null {
  if (!user) return null;
  const displayName =
    (user.user_metadata?.full_name as string | undefined) ||
    (user.user_metadata?.name as string | undefined) ||
    user.email?.split("@")[0] ||
    "Compliance Officer";

  return {
    badgeId: user.email ?? user.id,
    name: displayName,
    jurisdiction: "Legal Metrology Division",
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const supabase = useMemo(() => createClient(), []);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setIsLoading(false);
    });

    const { data: listener } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null);
      }
    );

    return () => listener.subscription.unsubscribe();
  }, [supabase]);

  const signInWithPassword = useCallback(
    async (email: string, password: string): Promise<AuthResult> => {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) return { ok: false, error: error.message };
      return { ok: true };
    },
    [supabase]
  );

  const signUpWithPassword = useCallback(
    async (email: string, password: string, name?: string): Promise<AuthResult> => {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: name ? { full_name: name } : undefined,
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });
      if (error) return { ok: false, error: error.message };
      // If email confirmation is required, Supabase returns a user but no session.
      const needsEmailConfirm = !data.session;
      return { ok: true, needsEmailConfirm };
    },
    [supabase]
  );

  const signInWithGoogle = useCallback(async (): Promise<AuthResult> => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    if (error) {
      const message = /unsupported provider|provider is not enabled/i.test(error.message)
        ? "Google sign-in is not enabled in Supabase yet. Please enable the Google provider in Supabase Authentication settings."
        : "Google sign-in could not be started. Please try again.";
      return { ok: false, error: message };
    }
    return { ok: true };
    // Browser navigates away to Google; nothing else to do here.
  }, [supabase]);

  const logout = useCallback(async () => {
    await supabase.auth.signOut();
    setUser(null);
  }, [supabase]);

  const deleteAccount = useCallback(async () => {
    const { data, error } = await supabase.auth.getSession();
    if (error || !data.session?.access_token) {
      throw new Error("Your session has expired. Please sign in again.");
    }
    await deleteAccountRequest(data.session.access_token);
    await supabase.auth.signOut();
    setUser(null);
  }, [supabase]);

  const officer = toOfficerSession(user);

  return (
    <AuthContext.Provider
      value={{
        officer,
        user,
        isLoading,
        signInWithPassword,
        signUpWithPassword,
        signInWithGoogle,
        logout,
        deleteAccount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
