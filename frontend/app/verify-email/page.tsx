import { fetchCurrentUser } from "@/lib/api";
import { VerifyEmailPanel } from "@/components/verify-email-panel";

export default async function VerifyEmailPage({
  searchParams
}: {
  searchParams: Promise<{ token?: string; email?: string; preview?: string }>;
}) {
  const session = await fetchCurrentUser().catch(() => null);
  const params = await searchParams;
  const email = params.email ?? session?.user.email ?? null;

  return (
    <div className="mx-auto grid max-w-6xl gap-8 px-4 py-14 sm:px-6 lg:grid-cols-[0.95fr_1.05fr] lg:px-8">
      <section className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
        <p className="text-sm uppercase tracking-[0.24em] text-brand">Verification</p>
        <h2 className="mt-4 text-4xl font-semibold tracking-tight">Keep account security lightweight, but real.</h2>
        <p className="mt-4 text-base leading-7 text-muted">
          CreatorLab sends verification links after signup and supports a local email preview in development, so you can test the exact user flow before plugging in a real mail provider.
        </p>
        <div className="mt-8 grid gap-4">
          {[
            "Secure verification tokens stored hashed in SQLite",
            "Resend flow for expired or missed emails",
            "Local preview support to keep Windows development simple"
          ].map((item) => (
            <div key={item} className="rounded-3xl border border-line/70 bg-canvas/60 px-4 py-4 text-sm">
              {item}
            </div>
          ))}
        </div>
      </section>

      <VerifyEmailPanel
        token={params.token}
        initialEmail={email}
        initialVerified={session?.user.email_verified ?? false}
        initialPreviewUrl={params.preview ?? null}
      />
    </div>
  );
}
