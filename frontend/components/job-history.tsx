"use client";

import { Download, Link2, LoaderCircle } from "lucide-react";
import { getDownloadUrl } from "@/lib/api";
import { JobRecord } from "@/lib/types";
import { formatBytes, formatRelativeTime } from "@/lib/utils";

const statusStyles = {
  queued: "bg-amber-500/10 text-amber-600 dark:text-amber-300",
  processing: "bg-sky-500/10 text-sky-700 dark:text-sky-300",
  completed: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  failed: "bg-rose-500/10 text-rose-700 dark:text-rose-300"
};

export function JobHistory({ jobs, title = "Recent jobs" }: { jobs: JobRecord[]; title?: string }) {
  return (
    <section className="rounded-[28px] border border-line/70 bg-panel/85 p-6 shadow-soft">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="text-sm text-muted">Track progress, retries, downloads, and finished results.</p>
        </div>
      </div>
      <div className="space-y-4">
        {jobs.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-line/70 px-4 py-10 text-center text-sm text-muted">
            No jobs yet. Run a tool and your processing history will appear here.
          </div>
        ) : (
          jobs.map((job) => (
            <article key={job.id} className="rounded-3xl border border-line/70 bg-canvas/60 p-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold capitalize">{job.tool.replaceAll("-", " ")}</span>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${statusStyles[job.status]}`}>
                      {job.status}
                    </span>
                    {(job.status === "queued" || job.status === "processing") && (
                      <LoaderCircle className="h-4 w-4 animate-spin text-brand" />
                    )}
                  </div>
                  <p className="text-xs text-muted">
                    {formatRelativeTime(job.created_at)} | Progress {job.progress}%
                  </p>
                  {job.input_files.length > 0 ? (
                    <p className="text-xs text-muted">
                      Inputs: {job.input_files.length} file{job.input_files.length > 1 ? "s" : ""}
                    </p>
                  ) : null}
                  {typeof job.meta.queue_position === "number" && job.meta.queue_position > 0 ? (
                    <p className="text-xs text-muted">Queue position: {job.meta.queue_position}</p>
                  ) : null}
                  {typeof job.meta.priority_score === "number" ? (
                    <p className="text-xs text-muted">Fair-share priority: {job.meta.priority_score}</p>
                  ) : null}
                  {typeof job.meta.attempt_count === "number" && Number(job.meta.attempt_count) > 0 ? (
                    <p className="text-xs text-muted">
                      Retries used: {job.meta.attempt_count} / {job.meta.max_retries ?? job.meta.attempt_count}
                    </p>
                  ) : null}
                  {job.error ? <p className="text-sm text-rose-500">{job.error}</p> : null}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {job.outputs.map((file) => (
                    <a
                      key={file.file_id}
                      href={getDownloadUrl(file.file_id)}
                      className="inline-flex items-center gap-2 rounded-full border border-line/70 bg-panel px-3 py-2 text-xs font-medium transition hover:border-brand/40"
                    >
                      <Download className="h-3.5 w-3.5" />
                      {file.filename}
                    </a>
                  ))}
                </div>
              </div>
              {job.outputs.length > 0 ? (
                <div className="mt-4 flex flex-wrap gap-3 text-xs text-muted">
                  {job.outputs.map((file) => (
                    <span key={file.file_id} className="inline-flex items-center gap-1">
                      <Link2 className="h-3.5 w-3.5" />
                      {formatBytes(file.size_bytes)}
                    </span>
                  ))}
                </div>
              ) : null}
            </article>
          ))
        )}
      </div>
    </section>
  );
}
