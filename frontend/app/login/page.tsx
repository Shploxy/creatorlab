import { redirect } from "next/navigation";
import { AuthForm } from "@/components/auth-form";
import { fetchCurrentUser } from "@/lib/api";

export default async function LoginPage({
  searchParams
}: {
  searchParams: Promise<{ verified?: string; reset?: string }>;
}) {
  const session = await fetchCurrentUser().catch(() => null);
  if (session) {
    redirect(session.user.email_verified ? "/account" : "/verify-email");
  }

  const params = await searchParams;
  const notices = [
    params.verified === "1" ? "Your email is verified. You can sign in now." : null,
    params.reset === "1" ? "Your password has been reset. Sign in with your new password." : null
  ].filter(Boolean);

  return (
    <div className="mx-auto grid max-w-6xl gap-8 px-4 py-14 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8">
      <section className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
        <p className="text-sm uppercase tracking-[0.24em] text-brand">Welcome back</p>
        <h2 className="mt-4 text-4xl font-semibold tracking-tight">Sign in and keep your workflow moving.</h2>
        <p className="mt-4 text-base leading-7 text-muted">
          Use your CreatorLab account to keep job history across backend restarts, track free-tier usage, and manage verification and password recovery cleanly.
        </p>
        {notices.length > 0 ? (
          <div className="mt-8 space-y-3">
            {notices.map((notice) => (
              <div key={notice} className="rounded-3xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-4 text-sm text-emerald-700 dark:text-emerald-300">
                {notice}
              </div>
            ))}
          </div>
        ) : null}
        <div className="mt-8 grid gap-4">
          {[
            "Persistent account-linked job tracking",
            "Verification and reset flows ready for public deployment",
            "Cookie-based auth that still runs simply on Windows"
          ].map((item) => (
            <div key={item} className="rounded-3xl border border-line/70 bg-canvas/60 px-4 py-4 text-sm">
              {item}
            </div>
          ))}
        </div>
      </section>

      <AuthForm mode="login" />
    </div>
  );
}
