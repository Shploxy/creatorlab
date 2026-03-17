import Link from "next/link";
import { fetchJobs, fetchPlans, fetchVisitorStatus, getDownloadUrl } from "@/lib/api";
import { JobHistory } from "@/components/job-history";
import { JobRecord } from "@/lib/types";
import { formatBytes } from "@/lib/utils";

export default async function DashboardPage() {
  let jobs: JobRecord[] = [];
  const visitorStatus = await fetchVisitorStatus().catch(() => null);
  const session = visitorStatus?.authenticated ? visitorStatus.user ?? null : null;
  const plans = await fetchPlans().catch(() => []);
  const currentPlan = session ? plans.find((plan) => plan.key === session.user.plan_key) ?? null : null;
  try {
    jobs = await fetchJobs();
  } catch {
    jobs = [];
  }

  const completed = jobs.filter((job) => job.status === "completed").length;
  const processing = jobs.filter((job) => job.status === "processing" || job.status === "queued").length;
  const files = jobs.flatMap((job) => job.outputs);
  const bytes = files.reduce((sum, file) => sum + file.size_bytes, 0);

  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <div className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
        <section className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
          <p className="text-sm uppercase tracking-[0.24em] text-brand">Recent jobs</p>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight">Pick up where this device left off</h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
            Review recent jobs, reopen downloads, and jump straight back into the tools. No signup is required for the normal workflow.
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            {[
              ["Completed jobs", String(completed)],
              ["Active queue", String(processing)],
              ["Output volume", formatBytes(bytes)]
            ].map(([label, value]) => (
              <div key={label} className="rounded-3xl border border-line/70 bg-canvas/60 p-5">
                <p className="text-sm text-muted">{label}</p>
                <p className="mt-2 text-2xl font-semibold">{value}</p>
              </div>
            ))}
          </div>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/tools" className="rounded-full bg-foreground px-5 py-3 text-sm font-medium text-canvas">
              Open tools
            </Link>
            <Link href="/history" className="rounded-full border border-line/70 bg-panel px-5 py-3 text-sm font-medium">
              Full history
            </Link>
            <Link href="/pricing" className="rounded-full border border-line/70 bg-panel px-5 py-3 text-sm font-medium">
              Upgrade options
            </Link>
          </div>
        </section>

        <section className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
          <h2 className="text-xl font-semibold">{session ? "Plan usage and downloads" : "Free usage and downloads"}</h2>
          {visitorStatus ? (
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              <div className="rounded-3xl border border-line/70 bg-canvas/60 p-4 text-sm">
                <p className="text-muted">{session ? "Plan" : "Mode"}</p>
                <p className="mt-2 font-medium">{session ? (currentPlan?.name ?? session.user.plan_key) : "Anonymous free"}</p>
              </div>
              <div className="rounded-3xl border border-line/70 bg-canvas/60 p-4 text-sm">
                <p className="text-muted">Jobs used</p>
                <p className="mt-2 font-medium">{session ? session.usage.jobs_used : visitorStatus.usage?.jobs_used ?? 0}</p>
              </div>
              <div className="rounded-3xl border border-line/70 bg-canvas/60 p-4 text-sm">
                <p className="text-muted">Remaining</p>
                <p className="mt-2 font-medium">
                  {session ? (session.usage.jobs_remaining ?? "Fair use") : visitorStatus.usage?.jobs_remaining ?? 0}
                </p>
              </div>
            </div>
          ) : null}
          <div className="mt-5 space-y-3">
            {files.length === 0 ? (
              <p className="rounded-3xl border border-dashed border-line/70 p-6 text-sm text-muted">No finished outputs yet.</p>
            ) : (
              files.slice(0, 6).map((file) => (
                <a
                  key={file.file_id}
                  href={getDownloadUrl(file.file_id)}
                  className="flex items-center justify-between rounded-3xl border border-line/70 bg-canvas/60 px-4 py-4 text-sm transition hover:border-brand/40"
                >
                  <span className="truncate">{file.filename}</span>
                  <span className="text-muted">{formatBytes(file.size_bytes)}</span>
                </a>
              ))
            )}
          </div>
        </section>
      </div>

      <div className="mt-8">
        <JobHistory jobs={jobs} />
      </div>
    </div>
  );
}
