"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { LoaderCircle } from "lucide-react";
import { toast } from "sonner";
import { resetPassword } from "@/lib/api";

export function ResetPasswordForm({ token }: { token?: string }) {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token) {
      setMessage("This reset link is missing or invalid.");
      return;
    }
    if (password !== confirmPassword) {
      setMessage("Your new password and confirmation do not match.");
      return;
    }

    try {
      setIsSubmitting(true);
      const result = await resetPassword(token, password);
      toast.success(result.message);
      router.push("/login?reset=1");
      router.refresh();
    } catch (error) {
      const nextMessage = error instanceof Error ? error.message : "We could not reset your password.";
      setMessage(nextMessage);
      toast.error(nextMessage);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!token) {
    return (
      <div className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
        <h1 className="text-3xl font-semibold tracking-tight">Reset your password</h1>
        <p className="mt-4 text-sm leading-6 text-muted">
          This page needs a valid reset token from your email. Request a fresh reset link to continue.
        </p>
        <Link href="/forgot-password" className="mt-8 inline-flex rounded-full bg-foreground px-5 py-3 text-sm font-medium text-canvas">
          Request a new reset link
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
      <h1 className="text-3xl font-semibold tracking-tight">Choose a new password</h1>
      <p className="mt-4 text-sm leading-6 text-muted">Use a strong password with at least 8 characters.</p>

      <div className="mt-8 space-y-5">
        <label className="block">
          <span className="mb-2 block text-sm font-medium">New password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            minLength={8}
            required
            className="w-full rounded-2xl border border-line/70 bg-canvas px-4 py-3 text-sm outline-none transition focus:border-brand/50"
          />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium">Confirm password</span>
          <input
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            minLength={8}
            required
            className="w-full rounded-2xl border border-line/70 bg-canvas px-4 py-3 text-sm outline-none transition focus:border-brand/50"
          />
        </label>
      </div>

      {message ? <p className="mt-5 text-sm text-rose-500">{message}</p> : null}

      <button
        type="submit"
        disabled={isSubmitting}
        className="mt-8 inline-flex w-full items-center justify-center gap-2 rounded-full bg-foreground px-5 py-3 text-sm font-medium text-canvas transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
        Reset password
      </button>
    </form>
  );
}
