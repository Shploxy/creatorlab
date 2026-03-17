"use client";

import { useState } from "react";
import { LoaderCircle } from "lucide-react";
import { toast } from "sonner";
import { requestPasswordReset } from "@/lib/api";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setIsSubmitting(true);
      const result = await requestPasswordReset(email);
      setMessage(result.message);
      setPreviewUrl(result.mail_preview_url ?? null);
      toast.success(result.message);
    } catch (error) {
      const nextMessage = error instanceof Error ? error.message : "We could not start the password reset flow.";
      setMessage(nextMessage);
      toast.error(nextMessage);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
      <h1 className="text-3xl font-semibold tracking-tight">Forgot your password?</h1>
      <p className="mt-4 text-sm leading-6 text-muted">
        Enter your email address and we will send you a secure link to choose a new password. In local development, CreatorLab can show you the saved preview instead of sending a real email.
      </p>

      <label className="mt-8 block">
        <span className="mb-2 block text-sm font-medium">Email</span>
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="w-full rounded-2xl border border-line/70 bg-canvas px-4 py-3 text-sm outline-none transition focus:border-brand/50"
          placeholder="you@example.com"
          required
        />
      </label>

      <button
        type="submit"
        disabled={isSubmitting}
        className="mt-8 inline-flex w-full items-center justify-center gap-2 rounded-full bg-foreground px-5 py-3 text-sm font-medium text-canvas transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
        Send reset link
      </button>

      {message ? <p className="mt-5 text-sm text-muted">{message}</p> : null}

      {previewUrl ? (
        <a
          href={previewUrl}
          target="_blank"
          rel="noreferrer"
          className="mt-5 inline-flex rounded-full border border-line/70 px-4 py-2 text-sm font-medium transition hover:border-brand/40"
        >
          Open local email preview
        </a>
      ) : null}
    </form>
  );
}
