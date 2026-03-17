"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { LoaderCircle } from "lucide-react";
import { toast } from "sonner";
import { logIn, signUp } from "@/lib/api";

type AuthMode = "login" | "signup";

export function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const isSignup = mode === "signup";

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      setIsSubmitting(true);
      setFormError(null);
      if (isSignup) {
        const session = await signUp({ email, password, full_name: fullName || undefined });
        toast.success(session.message ?? "Your account is ready.");
        if (session.requires_email_verification) {
          const searchParams = new URLSearchParams({ email });
          if (session.mail_preview_url) {
            searchParams.set("preview", session.mail_preview_url);
          }
          router.push(`/verify-email?${searchParams.toString()}`);
        } else {
          router.push("/account");
        }
      } else {
        await logIn({ email, password });
        toast.success("Welcome back.");
        router.push("/account");
      }
      router.refresh();
    } catch (error) {
      const nextMessage = error instanceof Error ? error.message : "We could not complete that request.";
      setFormError(nextMessage);
      toast.error(nextMessage);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
      <h1 className="text-3xl font-semibold tracking-tight">{isSignup ? "Create your CreatorLab account" : "Sign in to CreatorLab"}</h1>
      <p className="mt-4 text-sm leading-6 text-muted">
        {isSignup
          ? "Get persistent job history, free-tier usage tracking, and a smoother path to production deployment."
          : "Pick up where you left off with your saved plan, usage limits, and processed files."}
      </p>

      <div className="mt-8 space-y-5">
        {isSignup ? (
          <label className="block">
            <span className="mb-2 block text-sm font-medium">Full name</span>
            <input
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              className="w-full rounded-2xl border border-line/70 bg-canvas px-4 py-3 text-sm outline-none transition focus:border-brand/50"
              placeholder="Alex Rivera"
              autoComplete="name"
            />
          </label>
        ) : null}

        <label className="block">
          <span className="mb-2 block text-sm font-medium">Email</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full rounded-2xl border border-line/70 bg-canvas px-4 py-3 text-sm outline-none transition focus:border-brand/50"
            placeholder="you@example.com"
            autoComplete="email"
            required
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium">Password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-2xl border border-line/70 bg-canvas px-4 py-3 text-sm outline-none transition focus:border-brand/50"
            placeholder="At least 8 characters"
            autoComplete={isSignup ? "new-password" : "current-password"}
            minLength={8}
            required
          />
        </label>
      </div>

      {formError ? <p className="mt-5 text-sm text-rose-500">{formError}</p> : null}

      <button
        type="submit"
        disabled={isSubmitting}
        className="mt-8 inline-flex w-full items-center justify-center gap-2 rounded-full bg-foreground px-5 py-3 text-sm font-medium text-canvas transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
        {isSignup ? "Create account" : "Log in"}
      </button>

      <p className="mt-5 text-sm text-muted">
        {isSignup ? "Already have an account?" : "Need an account?"}{" "}
        <Link href={isSignup ? "/login" : "/signup"} className="font-medium text-foreground transition hover:text-brand">
          {isSignup ? "Log in" : "Sign up"}
        </Link>
      </p>
      {!isSignup ? (
        <p className="mt-2 text-sm text-muted">
          Forgot your password?{" "}
          <Link href="/forgot-password" className="font-medium text-foreground transition hover:text-brand">
            Reset it here
          </Link>
        </p>
      ) : null}
      {!isSignup ? (
        <p className="mt-2 text-sm text-muted">
          Need a new verification email?{" "}
          <Link href={email ? `/verify-email?email=${encodeURIComponent(email)}` : "/verify-email"} className="font-medium text-foreground transition hover:text-brand">
            Open verification help
          </Link>
        </p>
      ) : null}
    </form>
  );
}
