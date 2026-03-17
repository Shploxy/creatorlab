import { redirect } from "next/navigation";
import { AuthForm } from "@/components/auth-form";
import { fetchCurrentUser } from "@/lib/api";

export default async function SignupPage() {
  const session = await fetchCurrentUser().catch(() => null);
  if (session) {
    redirect(session.user.email_verified ? "/account" : "/verify-email");
  }

  return (
    <div className="mx-auto grid max-w-6xl gap-8 px-4 py-14 sm:px-6 lg:grid-cols-[0.95fr_1.05fr] lg:px-8">
      <section className="rounded-[32px] border border-brand/20 bg-brand px-8 py-10 text-white shadow-soft">
        <p className="text-sm uppercase tracking-[0.24em] text-white/70">Free plan</p>
        <h2 className="mt-4 text-4xl font-semibold tracking-tight">Create your account and verify your email with one clean flow.</h2>
        <p className="mt-4 text-base leading-7 text-white/80">
          CreatorLab now supports proper email verification, so the same local setup can grow into a real public-facing SaaS without reworking auth later.
        </p>
        <div className="mt-8 grid gap-4">
          {[
            "25 jobs per month on the free plan",
            "Verification emails with local dev previews",
            "Billing-ready structure for future upgrades"
          ].map((item) => (
            <div key={item} className="rounded-3xl border border-white/15 bg-white/10 px-4 py-4 text-sm">
              {item}
            </div>
          ))}
        </div>
      </section>

      <AuthForm mode="signup" />
    </div>
  );
}
