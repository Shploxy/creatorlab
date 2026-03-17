import Link from "next/link";
import { ForgotPasswordForm } from "@/components/forgot-password-form";

export default function ForgotPasswordPage() {
  return (
    <div className="mx-auto grid max-w-6xl gap-8 px-4 py-14 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8">
      <section className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
        <p className="text-sm uppercase tracking-[0.24em] text-brand">Recovery</p>
        <h2 className="mt-4 text-4xl font-semibold tracking-tight">Password recovery that works locally and in production.</h2>
        <p className="mt-4 text-base leading-7 text-muted">
          CreatorLab now sends secure reset links with expiring tokens, and the local mail preview makes the full flow easy to test on your development machine.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/login" className="rounded-full bg-foreground px-5 py-3 text-sm font-medium text-canvas">
            Back to login
          </Link>
          <Link href="/signup" className="rounded-full border border-line/70 bg-panel px-5 py-3 text-sm font-medium">
            Create account
          </Link>
        </div>
      </section>

      <ForgotPasswordForm />
    </div>
  );
}
