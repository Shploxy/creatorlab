"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { LoaderCircle, MailCheck } from "lucide-react";
import { toast } from "sonner";
import { fetchLatestDevMail, resendVerificationEmail, verifyEmailToken } from "@/lib/api";

type Props = {
  token?: string;
  initialEmail?: string | null;
  initialVerified?: boolean;
  initialPreviewUrl?: string | null;
};

const LOCAL_MAIL_STORAGE_PATH = String.raw`C:\Users\ll888\NewProject\backend\storage\mail`;

export function VerifyEmailPanel({
  token,
  initialEmail,
  initialVerified = false,
  initialPreviewUrl = null
}: Props) {
  const [status, setStatus] = useState<"idle" | "verifying" | "success" | "error">(
    token ? "verifying" : initialVerified ? "success" : "idle"
  );
  const [message, setMessage] = useState(
    initialVerified
      ? "Your email is already verified."
      : "Check your inbox for a verification link to finish setting up your CreatorLab account."
  );
  const [previewUrl, setPreviewUrl] = useState<string | null>(initialPreviewUrl);
  const [email, setEmail] = useState(initialEmail ?? "");
  const [isResending, setIsResending] = useState(false);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;
    setStatus("verifying");
    verifyEmailToken(token)
      .then((result) => {
        if (cancelled) return;
        setStatus("success");
        setMessage(result.message);
        toast.success(result.message);
      })
      .catch((error) => {
        if (cancelled) return;
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "We could not verify that email.");
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  useEffect(() => {
    if (!email || token || initialVerified) return;
    fetchLatestDevMail(email, "email_verification")
      .then((mail) => setPreviewUrl(mail?.preview_url ?? null))
      .catch(() => setPreviewUrl(null));
  }, [email, token, initialVerified]);

  async function handleResend() {
    try {
      setIsResending(true);
      const result = await resendVerificationEmail(email ? { email } : {});
      setMessage(result.message);
      setPreviewUrl(result.mail_preview_url ?? null);
      toast.success(result.message);
    } catch (error) {
      const nextMessage = error instanceof Error ? error.message : "We could not resend the verification email.";
      setMessage(nextMessage);
      toast.error(nextMessage);
    } finally {
      setIsResending(false);
    }
  }

  return (
    <div className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
      <div className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-brand.soft text-brand">
        {status === "verifying" ? <LoaderCircle className="h-6 w-6 animate-spin" /> : <MailCheck className="h-6 w-6" />}
      </div>
      <h1 className="mt-6 text-3xl font-semibold tracking-tight">
        {status === "success" ? "Email verified" : token ? "Verifying your email" : "Verify your email"}
      </h1>
      <p className="mt-4 text-sm leading-6 text-muted">{message}</p>
      {status === "success" ? (
        <p className="mt-3 text-sm text-muted">
          Next step: head to your account or dashboard and start using CreatorLab with your verified session.
        </p>
      ) : null}

      {!token && !initialVerified ? (
        <div className="mt-8 space-y-4">
          <label className="block">
            <span className="mb-2 block text-sm font-medium">Email address</span>
            <input
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              type="email"
              placeholder="you@example.com"
              className="w-full rounded-2xl border border-line/70 bg-canvas px-4 py-3 text-sm outline-none transition focus:border-brand/50"
            />
          </label>
          <button
            type="button"
            onClick={handleResend}
            disabled={isResending || !email}
            className="inline-flex items-center gap-2 rounded-full bg-foreground px-5 py-3 text-sm font-medium text-canvas transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isResending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
            Resend verification email
          </button>
        </div>
      ) : null}

      {previewUrl ? (
        <div className="mt-8 rounded-[24px] border border-brand/20 bg-brand.soft p-5 text-sm">
          <p className="font-medium text-foreground">Local dev mail preview</p>
          <p className="mt-2 leading-6 text-muted">
            CreatorLab is currently using the local file mail provider, so this verification email was saved on disk instead
            of being sent through a real email service.
          </p>
          <p className="mt-3 rounded-2xl border border-line/70 bg-canvas/80 px-3 py-2 font-mono text-xs text-foreground">
            {LOCAL_MAIL_STORAGE_PATH}
          </p>
          <p className="mt-3 text-muted">
            Each message is stored as a JSON file in that folder. You can open the latest preview in your browser or inspect
            the saved file directly from the project folder.
          </p>
          <a href={previewUrl} target="_blank" rel="noreferrer" className="mt-4 inline-flex rounded-full border border-line/70 px-4 py-2 font-medium transition hover:border-brand/40">
            Open email preview
          </a>
        </div>
      ) : null}

      <div className="mt-8 flex flex-wrap gap-3">
        <Link href="/account" className="rounded-full bg-foreground px-5 py-3 text-sm font-medium text-canvas">
          Open account
        </Link>
        <Link href="/login" className="rounded-full border border-line/70 bg-panel px-5 py-3 text-sm font-medium">
          Go to login
        </Link>
      </div>
    </div>
  );
}
