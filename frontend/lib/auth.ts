import { createClient } from "@/lib/supabase/client";

export async function signIn(email: string, password: string) {
  return createClient().auth.signInWithPassword({ email, password });
}

export async function signUp(email: string, password: string, name?: string) {
  return createClient().auth.signUp({
    email,
    password,
    options: {
      data: name ? { full_name: name } : undefined,
      emailRedirectTo: typeof window === "undefined" ? undefined : `${window.location.origin}/auth/callback`,
    },
  });
}

export async function signOut() {
  return createClient().auth.signOut();
}

export async function getSession() {
  return createClient().auth.getSession();
}

export async function getUser() {
  return createClient().auth.getUser();
}
