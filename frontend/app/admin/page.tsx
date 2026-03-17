import { AlertTriangle, CheckCircle2, Database, Files } from "lucide-react";
import { fetchAdminSummary, fetchJobsPage } from "@/lib/api";
import { JobHistory } from "@/components/job-history";
import { AdminSummary } from "@/lib/types";
import { formatBytes, formatDurationSeconds } from "@/lib/utils";

export default async function AdminPage({
  searchParams
}: {
  searchParams: Promise<{ status?: string; tool?: string; page?: string }>;
}) {
  const params = await searchParams;
  let summary: AdminSummary | null = null;
  let filteredJobs = [];
  try {
    summary = await fetchAdminSummary();
  } catch {
    summary = null;
  }
  try {
    const page = Number(params.page ?? "1") || 1;
    const result = await fetchJobsPage({
      page,
      pageSize: 10,
      status: params.status,
      tool: params.tool
    });
    filteredJobs = result.items;
  } catch {
    filteredJobs = summary?.recent_jobs ?? [];
  }

  const metrics = summary
    ? [
        { label: "Total jobs", value: String(summary.total_jobs), icon: Files },
        { label: "Completed", value: String(summary.completed_jobs), icon: CheckCircle2 },
        { label: "Failed", value: String(summary.failed_jobs), icon: AlertTriangle },
        { label: "Storage", value: formatBytes(summary.storage_usage_bytes), icon: Database },
        { label: "Runtime", value: summary.runtime?.device?.toUpperCase() ?? "CPU", icon: Database },
        { label: "Queue depth", value: String(summary.queue_depth ?? 0), icon: Files },
        { label: "Workers", value: String(summary.worker_threads ?? 0), icon: Files },
        { label: "Queue groups", value: String(summary.queue_groups ?? 0), icon: Files },
        { label: "Active sessions", value: String(summary.auth?.active_sessions ?? 0), icon: Files }
      ]
    : [];

  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
        <p className="text-sm uppercase tracking-[0.24em] text-brand">Admin</p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight">Operational snapshot</h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
          Use this page to monitor recent jobs, failures, processed volume, and local storage usage in demo mode.
        </p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {metrics.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-line/70 p-6 text-sm text-muted">Backend summary is not available yet.</div>
          ) : (
            metrics.map((metric) => (
              <div key={metric.label} className="rounded-3xl border border-line/70 bg-canvas/60 p-5">
                <metric.icon className="h-5 w-5 text-brand" />
                <p className="mt-4 text-sm text-muted">{metric.label}</p>
                <p className="mt-2 text-2xl font-semibold">{metric.value}</p>
              </div>
            ))
          )}
        </div>
      </section>

      {summary ? (
        <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_0.9fr]">
          <div className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
            <h2 className="text-xl font-semibold">System stats</h2>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <div className="rounded-3xl border border-line/70 bg-canvas/60 p-4 text-sm">
                <p className="text-muted">Oldest queued job</p>
                <p className="mt-2 font-medium">{formatDurationSeconds(summary.oldest_queued_seconds)}</p>
              </div>
              <div className="rounded-3xl border border-line/70 bg-canvas/60 p-4 text-sm">
                <p className="text-muted">Mail previews</p>
                <p className="mt-2 font-medium">
                  {(summary.mail?.message_count ?? 0).toString()} via {summary.mail?.backend ?? "n/a"}
                </p>
              </div>
              <div className="rounded-3xl border border-line/70 bg-canvas/60 p-4 text-sm">
                <p className="text-muted">Pending auth tokens</p>
                <p className="mt-2 font-medium">
                  {(summary.auth?.pending_tokens?.email_verification ?? 0) + (summary.auth?.pending_tokens?.password_reset ?? 0)}
                </p>
              </div>
              <div className="rounded-3xl border border-line/70 bg-canvas/60 p-4 text-sm">
                <p className="text-muted">Cleanup</p>
                <p className="mt-2 font-medium">
                  {(summary.cleanup?.deleted_files ?? 0).toString()} files, {formatBytes(Number(summary.cleanup?.deleted_bytes ?? 0))}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
            <h2 className="text-xl font-semibold">Storage breakdown</h2>
            <div className="mt-6 space-y-3">
              {Object.entries(summary.storage_breakdown ?? {}).length === 0 ? (
                <p className="rounded-3xl border border-dashed border-line/70 p-6 text-sm text-muted">Storage details are not available yet.</p>
              ) : (
                Object.entries(summary.storage_breakdown ?? {}).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between rounded-2xl border border-line/70 bg-canvas/60 px-4 py-3 text-sm">
                    <span className="capitalize text-muted">{key.replaceAll("_", " ")}</span>
                    <span className="font-medium">{formatBytes(value)}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      ) : null}

      <div className="mt-8">
        <JobHistory jobs={filteredJobs} title="Operational job feed" />
      </div>
    </div>
  );
}
