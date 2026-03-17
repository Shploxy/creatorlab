import Link from "next/link";
import { fetchCurrentUser, fetchJobsPage, fetchPlans } from "@/lib/api";
import { JobHistory } from "@/components/job-history";
import { formatRelativeTime } from "@/lib/utils";

export default async function AccountPage() {
  const session = await fetchCurrentUser().catch(() => null);

  if (!session) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-14 sm:px-6 lg:px-8">
        <section className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
          <p className="text-sm uppercase tracking-[0.24em] text-brand">Account</p>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight">Sign in to unlock persistent usage tracking.</h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
            CreatorLab still works in local demo mode, but accounts unlock saved history, monthly usage limits, and a billing-ready structure that can grow with the product.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/login" className="rounded-full bg-foreground px-5 py-3 text-sm font-medium text-canvas">
              Log in
            </Link>
            <Link href="/signup" className="rounded-full border border-line/70 bg-panel px-5 py-3 text-sm font-medium">
              Create free account
            </Link>
          </div>
        </section>
      </div>
    );
  }

  const plans = await fetchPlans().catch(() => []);
  const currentPlan = plans.find((plan) => plan.key === session.user.plan_key) ?? null;
  const history = await fetchJobsPage({ page: 1, pageSize: 6, mine: true }).catch(() => ({
    items: [],
    total: 0,
    page: 1,
    page_size: 6
  }));

  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      {!session.user.email_verified ? (
        <section className="mb-8 rounded-[28px] border border-amber-500/20 bg-amber-500/10 p-6 shadow-soft">
          <p className="text-sm uppercase tracking-[0.24em] text-amber-700 dark:text-amber-300">Email verification needed</p>
          <h2 className="mt-3 text-2xl font-semibold">Verify your email to unlock the full account flow.</h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-muted">
            Your account is ready. Confirm your email to make sign-in smoother, unlock stricter deployment settings, and keep future paid upgrades attached to a verified account.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href={`/verify-email?email=${encodeURIComponent(session.user.email)}`} className="rounded-full bg-foreground px-5 py-3 text-sm font-medium text-canvas">
              Verify email
            </Link>
            <Link href="/login" className="rounded-full border border-line/70 bg-panel px-5 py-3 text-sm font-medium">
              Open login
            </Link>
          </div>
        </section>
      ) : null}

      <section className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-brand">Account</p>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight">{session.user.full_name || session.user.email}</h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
              You joined on {formatRelativeTime(session.user.created_at)} and you are currently on the {currentPlan?.name ?? "Free"} plan.
            </p>
          </div>
          <div className="rounded-[28px] border border-brand/20 bg-brand px-6 py-5 text-white shadow-soft">
            <p className="text-sm uppercase tracking-[0.22em] text-white/70">Current plan</p>
            <p className="mt-3 text-2xl font-semibold">{currentPlan?.name ?? "Free"}</p>
            <p className="mt-2 text-sm text-white/80">{currentPlan?.description ?? "Version 1 plan details are loading."}</p>
          </div>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <div className="rounded-3xl border border-line/70 bg-canvas/60 p-5">
            <p className="text-sm text-muted">Jobs used this month</p>
            <p className="mt-2 text-3xl font-semibold">{session.usage.jobs_used}</p>
          </div>
          <div className="rounded-3xl border border-line/70 bg-canvas/60 p-5">
            <p className="text-sm text-muted">Plan limit</p>
            <p className="mt-2 text-3xl font-semibold">{session.usage.jobs_limit ?? "Fair use"}</p>
          </div>
          <div className="rounded-3xl border border-line/70 bg-canvas/60 p-5">
            <p className="text-sm text-muted">Remaining this month</p>
            <p className="mt-2 text-3xl font-semibold">{session.usage.jobs_remaining ?? "Priority fair use"}</p>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/pricing" className="rounded-full bg-foreground px-5 py-3 text-sm font-medium text-canvas">
            View plans
          </Link>
          <Link href="/tools" className="rounded-full border border-line/70 bg-panel px-5 py-3 text-sm font-medium">
            Run a tool
          </Link>
        </div>
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_0.9fr]">
        <div className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
          <h2 className="text-2xl font-semibold">Plan benefits</h2>
          <div className="mt-6 space-y-3">
            {(currentPlan?.features ?? []).map((feature) => (
              <div key={feature} className="rounded-2xl border border-line/70 bg-canvas/60 px-4 py-3 text-sm">
                {feature}
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
          <h2 className="text-2xl font-semibold">Billing status</h2>
          <p className="mt-4 text-sm leading-6 text-muted">
            Payments are not live yet, but the plan and billing API structure is already in place so Stripe checkout can be added without reworking your account model.
          </p>
          <div className="mt-6 rounded-[24px] border border-dashed border-line/70 p-5 text-sm text-muted">
            No active paid subscription yet. CreatorLab is ready for a future upgrade flow.
          </div>
        </div>
      </section>

      <div className="mt-8">
        <JobHistory jobs={history.items} title={`Your recent jobs (${history.total})`} />
      </div>
    </div>
  );
}
