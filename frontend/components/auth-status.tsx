"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { logOut } from "@/lib/api";
import { AuthSessionResponse } from "@/lib/types";

export function AuthStatus({ initialSession }: { initialSession: AuthSessionResponse | null }) {
  const router = useRouter();
  const [session, setSession] = useState<AuthSessionResponse | null>(initialSession);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    setSession(initialSession);
  }, [initialSession]);

  async function handleLogout() {
    try {
      setIsLoggingOut(true);
      await logOut();
      setSession(null);
      toast.success("Signed out.");
      router.push("/");
      router.refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not sign out.");
    } finally {
      setIsLoggingOut(false);
    }
  }

  if (!session) {
    return null;
  }

  return (
    <div className="hidden items-center gap-3 md:flex">
      <Link href={session.user.email_verified ? "/dashboard" : "/verify-email"} className="text-sm text-muted transition hover:text-foreground">
        {session.user.email_verified ? "Dashboard" : "Verify email"}
      </Link>
      <Link href="/account" className="text-sm text-muted transition hover:text-foreground">
        Account
      </Link>
      {!session.user.email_verified ? (
        <Link
          href={`/verify-email?email=${encodeURIComponent(session.user.email)}`}
          className="rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 text-xs font-medium text-amber-700 dark:text-amber-300"
        >
          Verify email
        </Link>
      ) : null}
      <button
        type="button"
        onClick={handleLogout}
        disabled={isLoggingOut}
        className="rounded-full border border-line/70 px-4 py-2 text-sm transition hover:border-brand/40 disabled:opacity-60"
      >
        {isLoggingOut ? "Signing out..." : "Log out"}
      </button>
    </div>
  );
}
