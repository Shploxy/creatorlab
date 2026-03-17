import Link from "next/link";
import { ArrowRight, CreditCard, ShieldCheck } from "lucide-react";
import { SectionHeading } from "@/components/section-heading";
import { fetchPlans } from "@/lib/api";

export default async function PricingPage() {
  const plans = await fetchPlans().catch(() => []);

  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
        <SectionHeading
          eyebrow="Pricing"
          title="Start free, upgrade only when the extra headroom is worth it"
          description="CreatorLab is designed so free users can do useful work immediately. Paid plans are for heavier usage, faster processing, and convenience, not to block the basics."
        />
      </section>

      <div className="mt-8 grid gap-6 xl:grid-cols-3">
        {plans.map((plan) => (
          <section
            key={plan.key}
            className={`rounded-[32px] border p-8 shadow-soft ${
              plan.key === "creator" ? "border-brand/30 bg-brand text-white" : "border-line/70 bg-panel/85"
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className={`text-sm uppercase tracking-[0.24em] ${plan.key === "creator" ? "text-white/70" : "text-brand"}`}>{plan.name}</p>
                <h2 className="mt-4 text-3xl font-semibold">{plan.monthly_price_usd === 0 ? "Free" : `$${plan.monthly_price_usd}/mo`}</h2>
              </div>
              {plan.key === "creator" ? <span className="rounded-full bg-white/15 px-3 py-1 text-xs font-semibold">Best value</span> : null}
            </div>
            <p className={`mt-5 text-sm leading-6 ${plan.key === "creator" ? "text-white/80" : "text-muted"}`}>{plan.description}</p>
            <div className="mt-8 rounded-[24px] border border-current/15 bg-black/5 px-4 py-4">
              <p className={`text-sm ${plan.key === "creator" ? "text-white/80" : "text-muted"}`}>Usage allowance</p>
              <p className="mt-2 text-2xl font-semibold">{plan.monthly_jobs ?? "Fair use"} jobs / month</p>
            </div>
            <div className="mt-8 space-y-3">
              {plan.features.map((feature) => (
                <div key={feature} className={`rounded-2xl border px-4 py-3 text-sm ${plan.key === "creator" ? "border-white/15 bg-white/10" : "border-line/70 bg-canvas/60"}`}>
                  {feature}
                </div>
              ))}
            </div>
            <Link
              href={plan.monthly_price_usd === 0 ? "/tools" : "/account"}
              className={`mt-8 inline-flex items-center gap-2 rounded-full px-5 py-3 text-sm font-medium transition ${
                plan.key === "creator" ? "bg-white text-brand hover:opacity-90" : "bg-foreground text-canvas hover:opacity-90"
              }`}
            >
              {plan.monthly_price_usd === 0 ? "Use free tools now" : "See optional upgrade path"}
              <ArrowRight className="h-4 w-4" />
            </Link>
          </section>
        ))}
      </div>

      <section className="mt-8 grid gap-6 lg:grid-cols-2">
        <div className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
          <div className="flex items-center gap-3">
            <CreditCard className="h-5 w-5 text-brand" />
            <h3 className="text-lg font-semibold">Billing-ready architecture</h3>
          </div>
          <p className="mt-4 text-sm leading-6 text-muted">
            CreatorLab already has plan definitions, usage tracking, and placeholder billing endpoints, so Stripe checkout and subscription sync can be added later without turning today&apos;s product into a forced-signup experience.
          </p>
        </div>
        <div className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
          <div className="flex items-center gap-3">
            <ShieldCheck className="h-5 w-5 text-brand" />
            <h3 className="text-lg font-semibold">Local-first by default</h3>
          </div>
          <p className="mt-4 text-sm leading-6 text-muted">
            You can run the same app on a Windows laptop for development, then move into Docker and a reverse proxy when it is time to deploy publicly, while keeping the user flow lightweight.
          </p>
        </div>
      </section>
    </div>
  );
}
