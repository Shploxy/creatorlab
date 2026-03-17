"use client";

import { useEffect, useMemo, useState } from "react";
import { type Accept, type FileRejection, useDropzone } from "react-dropzone";
import { toast } from "sonner";
import { CheckCircle2, Copy, FileUp, LoaderCircle, ShieldAlert, Sparkles } from "lucide-react";
import { createJob, fetchJob, fetchVisitorStatus, getDownloadUrl, resolveApiUrl } from "@/lib/api";
import { ToolDefinition, JobRecord, VisitorStatus } from "@/lib/types";
import { formatBytes } from "@/lib/utils";

type Props = {
  tool: ToolDefinition;
  initialJobs: JobRecord[];
};

const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024;
const MAX_BATCH_SIZE_BYTES = 80 * 1024 * 1024;

export function ToolWorkbench({ tool, initialJobs }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const [job, setJob] = useState<JobRecord | null>(initialJobs[0] ?? null);
  const [jobs, setJobs] = useState<JobRecord[]>(initialJobs);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pageRange, setPageRange] = useState("1-2");
  const [pdfSplitMode, setPdfSplitMode] = useState<"range" | "chunks">("range");
  const [chunkSize, setChunkSize] = useState("4");
  const [qualityMode, setQualityMode] = useState<"standard" | "high_quality">("standard");
  const [selectedPreviewUrls, setSelectedPreviewUrls] = useState<string[]>([]);
  const [visitorStatus, setVisitorStatus] = useState<VisitorStatus | null>(null);

  const accept = useMemo<Accept>(() => {
    if (tool.accept.includes(".pdf")) {
      return { "application/pdf": [".pdf"] } as Accept;
    }

    return {
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
      "image/webp": [".webp"]
    } as Accept;
  }, [tool.accept]);

  const onDrop = (acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
    if (rejectedFiles.length) {
      const reason = rejectedFiles[0]?.errors?.[0]?.message ?? "Check type and size constraints.";
      toast.error(`Some files were rejected. ${reason}`);
    }
    setFiles(acceptedFiles.slice(0, tool.maxFiles));
  };

  const dropzone = useDropzone({
    onDrop,
    maxFiles: tool.maxFiles,
    accept,
    maxSize: MAX_FILE_SIZE_BYTES,
    disabled: tool.available === false
  });

  useEffect(() => {
    fetchVisitorStatus()
      .then(setVisitorStatus)
      .catch(() => setVisitorStatus(null));
  }, []);

  useEffect(() => {
    const nextUrls = files
      .filter((file) => file.type.startsWith("image/"))
      .map((file) => URL.createObjectURL(file));
    setSelectedPreviewUrls(nextUrls);
    return () => nextUrls.forEach((url) => URL.revokeObjectURL(url));
  }, [files]);

  useEffect(() => {
    if (!job || job.status === "completed" || job.status === "failed") return;
    const interval = window.setInterval(async () => {
      try {
        const updated = await fetchJob(job.id);
        setJob(updated);
        setJobs((current) => [updated, ...current.filter((item) => item.id !== updated.id)]);
      } catch {
        // Quiet polling.
      }
    }, 1800);
    return () => window.clearInterval(interval);
  }, [job]);

  async function handleSubmit() {
    if (!files.length) {
      toast.error("Add at least one valid file to continue.");
      return;
    }
    if (tool.available === false) {
      toast.error("This feature is coming soon and cannot be submitted yet.");
      return;
    }
    const totalBytes = files.reduce((sum, file) => sum + file.size, 0);
    if (totalBytes > MAX_BATCH_SIZE_BYTES) {
      toast.error("The combined upload is too large. Use a smaller batch and try again.");
      return;
    }

    const fields: Record<string, string> = {};
    if (tool.slug === "pdf-split") {
      fields.mode = pdfSplitMode;
      if (pdfSplitMode === "range") {
        fields.page_ranges = pageRange;
      } else {
        const normalizedChunkSize = Number.parseInt(chunkSize, 10);
        fields.chunk_size = Number.isFinite(normalizedChunkSize) && normalizedChunkSize > 0 ? String(normalizedChunkSize) : "2";
      }
    }
    if (tool.slug === "upscale") fields.quality_mode = qualityMode;

    try {
      setIsSubmitting(true);
      const created = await createJob(tool.endpoint, files, fields);
      setJob(created);
      setJobs((current) => [created, ...current]);
      toast.success("Job started. We are processing your files now.");
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : typeof error === "object" && error && "message" in error && typeof error.message === "string"
            ? error.message
            : "Something went wrong";
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  const latestImageOutput = job?.outputs.find((output) => output.content_type.startsWith("image/"));
  const zipOutput = job?.outputs.find((output) => output.content_type === "application/zip");
  const fileOutputs = job?.outputs.filter((output) => !output.meta.bundle) ?? [];
  const compressionMeta = job?.outputs[0]?.meta;
  const totalSelectedBytes = files.reduce((sum, file) => sum + file.size, 0);
  const statusMessage =
    job?.status === "queued"
      ? typeof job.meta.queue_position === "number" && job.meta.queue_position > 0
        ? `Queued fairly across users. Current position: ${job.meta.queue_position}.`
        : "Queued and waiting for an available worker."
      : job?.status === "processing"
        ? "Processing is running in the background. You can stay on this page and watch the progress update."
        : job?.status === "completed"
          ? "Processing finished successfully. Your files are ready to preview or download."
          : job?.status === "failed"
            ? "This run failed. Review the message below and try again with a smaller or cleaner input if needed."
            : "Drop files to begin. CreatorLab will validate the upload before starting a job.";

  async function copyShareLink(fileId: string) {
    try {
      await navigator.clipboard.writeText(getDownloadUrl(fileId));
      toast.success("Share link copied.");
    } catch {
      toast.error("Could not copy the share link.");
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
      <section className="rounded-[28px] border border-line/70 bg-panel/85 p-6 shadow-soft">
        <div className="flex flex-wrap items-center gap-3">
          <span className="rounded-full bg-brand.soft px-3 py-1 text-xs font-semibold text-brand">{tool.badge}</span>
          <span className="text-xs uppercase tracking-[0.24em] text-muted">{tool.category}</span>
        </div>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight">{tool.title}</h1>
        <p className="mt-3 max-w-2xl text-base leading-7 text-muted">{tool.details}</p>

        {tool.available === false ? (
          <div className="mt-6 rounded-[24px] border border-amber-500/20 bg-amber-500/10 p-5">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/70 text-amber-700 dark:bg-canvas/70 dark:text-amber-300">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">Coming soon</p>
                <p className="mt-2 text-sm leading-6 text-muted">
                  AI enhancement in progress. The upscale architecture is staying in CreatorLab, but public submissions are paused until the results are reliable enough to trust.
                </p>
              </div>
            </div>
          </div>
        ) : null}

        {visitorStatus ? (
          <div className="mt-6 rounded-[24px] border border-line/70 bg-canvas/60 p-5 text-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-muted">{visitorStatus.authenticated ? "Account usage this month" : "This device this month"}</p>
                <p className="mt-1 font-medium">
                  {visitorStatus.authenticated
                    ? `${visitorStatus.user?.usage.jobs_used ?? 0} of ${visitorStatus.user?.usage.jobs_limit ?? "fair use"} jobs used`
                    : `${visitorStatus.usage?.jobs_used ?? 0} of ${visitorStatus.usage?.jobs_limit ?? 0} jobs used`}
                </p>
              </div>
              <div className="text-right">
                <p className="text-muted">{visitorStatus.authenticated ? "Plan" : "Account"}</p>
                <p className="mt-1 font-medium capitalize">
                  {visitorStatus.authenticated ? visitorStatus.user?.user.plan_key : "Not required"}
                </p>
              </div>
            </div>
            {!visitorStatus.authenticated ? (
              <div className="mt-3 space-y-2 text-muted">
                <p>No signup required. CreatorLab keeps recent jobs on this device and only suggests an account later if you want higher limits or cross-device history.</p>
                {(visitorStatus.usage?.jobs_remaining ?? 0) <= 10 ? (
                  <p>
                    You&apos;re getting close to the free device limit. If you need more headroom later, the upgrade path is optional and starts on the pricing page.
                  </p>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}

        <div
          {...dropzone.getRootProps()}
          className={`mt-8 rounded-[28px] border border-dashed p-8 text-center transition ${
            tool.available === false
              ? "cursor-not-allowed border-amber-500/20 bg-amber-500/5 opacity-80"
              : "border-line/80 bg-canvas/60 hover:border-brand/50"
          }`}
        >
          <input {...dropzone.getInputProps()} />
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-brand.soft text-brand">
            <FileUp className="h-7 w-7" />
          </div>
          <h2 className="mt-4 text-lg font-semibold">{tool.available === false ? "Feature reopening soon" : "Drop files here or click to browse"}</h2>
          <p className="mt-2 text-sm text-muted">
            {tool.available === false
              ? "The launch flow is intentionally paused while AI enhancement is being improved."
              : `Accepts ${tool.accept.join(", ")} | up to ${tool.maxFiles} file${tool.maxFiles > 1 ? "s" : ""}`}
          </p>
          <p className="mt-2 text-xs uppercase tracking-[0.18em] text-muted">
            {tool.available === false ? "Coming soon | AI enhancement in progress" : "25 MB per file | 80 MB per batch"}
          </p>
        </div>

        {tool.slug === "pdf-split" ? (
          <div className="mt-6 rounded-[24px] border border-line/70 bg-canvas/60 p-5">
            <p className="text-sm font-medium">Split mode</p>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <button
                type="button"
                onClick={() => setPdfSplitMode("range")}
                className={`rounded-2xl border px-4 py-4 text-left text-sm transition ${
                  pdfSplitMode === "range" ? "border-brand/40 bg-brand.soft" : "border-line/70 bg-panel/80"
                }`}
              >
                <p className="font-medium">Extract page range</p>
                <p className="mt-2 text-muted">Create one PDF output from a chosen range such as 1-3 or 5-8.</p>
              </button>
              <button
                type="button"
                onClick={() => setPdfSplitMode("chunks")}
                className={`rounded-2xl border px-4 py-4 text-left text-sm transition ${
                  pdfSplitMode === "chunks" ? "border-brand/40 bg-brand.soft" : "border-line/70 bg-panel/80"
                }`}
              >
                <p className="font-medium">Split into chunks</p>
                <p className="mt-2 text-muted">Create multiple PDFs by splitting the file every N pages.</p>
              </button>
            </div>

            {pdfSplitMode === "range" ? (
              <label className="mt-5 block">
                <span className="mb-2 block text-sm font-medium">Page range</span>
                <input
                  value={pageRange}
                  onChange={(event) => setPageRange(event.target.value)}
                  placeholder="Example: 1-3"
                  className="w-full rounded-2xl border border-line/70 bg-canvas px-4 py-3 text-sm outline-none transition focus:border-brand/50"
                />
              </label>
            ) : (
              <label className="mt-5 block">
                <span className="mb-2 block text-sm font-medium">Split every N pages</span>
                <input
                  value={chunkSize}
                  onChange={(event) => setChunkSize(event.target.value)}
                  inputMode="numeric"
                  placeholder="Example: 4"
                  className="w-full rounded-2xl border border-line/70 bg-canvas px-4 py-3 text-sm outline-none transition focus:border-brand/50"
                />
              </label>
            )}
          </div>
        ) : null}

        {tool.slug === "upscale" && tool.available !== false ? (
          <div className="mt-6 rounded-[24px] border border-line/70 bg-canvas/60 p-5">
            <p className="text-sm font-medium">AI mode</p>
            <p className="mt-2 text-sm text-muted">
              Standard AI is the default for local stability. High Quality AI keeps the x4 path for stronger machines and may
              automatically fall back if resources are limited.
            </p>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <button
                type="button"
                onClick={() => setQualityMode("standard")}
                className={`rounded-2xl border px-4 py-4 text-left text-sm transition ${
                  qualityMode === "standard" ? "border-brand/40 bg-brand.soft" : "border-line/70 bg-panel/80"
                }`}
              >
                <p className="font-medium">Standard AI (fast, 2x)</p>
                <p className="mt-2 text-muted">Best default for CPU and normal laptops. Optimized for speed, stability, and queue fairness.</p>
              </button>
              <button
                type="button"
                onClick={() => setQualityMode("high_quality")}
                className={`rounded-2xl border px-4 py-4 text-left text-sm transition ${
                  qualityMode === "high_quality" ? "border-brand/40 bg-brand.soft" : "border-line/70 bg-panel/80"
                }`}
              >
                <p className="font-medium">High Quality AI (4x)</p>
                <p className="mt-2 text-muted">Requires more resources. Best with CUDA/GPU. CreatorLab may fall back to Standard AI to keep jobs stable.</p>
              </button>
            </div>
          </div>
        ) : null}

        <div className="mt-6 space-y-3">
          {files.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-line/70 bg-canvas/40 px-4 py-5 text-sm text-muted">
              No files selected yet. Add a valid file to see previews, limits, and queue estimates here.
            </div>
          ) : (
            files.map((file) => (
              <div key={`${file.name}-${file.lastModified}`} className="flex items-center justify-between rounded-2xl border border-line/70 bg-canvas/70 px-4 py-3 text-sm">
                <span className="truncate">{file.name}</span>
                <span className="text-muted">{formatBytes(file.size)}</span>
              </div>
            ))
          )}
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting || tool.available === false}
            className="inline-flex items-center gap-2 rounded-full bg-foreground px-5 py-3 text-sm font-medium text-canvas transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
            {tool.available === false ? "Coming soon" : "Start processing"}
          </button>
          <p className="text-sm text-muted">Estimated time: {tool.eta}</p>
          {tool.slug === "upscale" && tool.available !== false ? (
            <p className="text-sm text-muted">{qualityMode === "standard" ? "Fast AI mode selected" : "High-quality AI selected"}</p>
          ) : null}
          {files.length > 0 ? <p className="text-sm text-muted">Selected: {formatBytes(totalSelectedBytes)}</p> : null}
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <div className="rounded-3xl border border-line/70 bg-canvas/60 p-4 text-sm">
            <p className="text-muted">Upload constraints</p>
            <p className="mt-2 font-medium">
              Max {tool.maxFiles} file{tool.maxFiles > 1 ? "s" : ""} | {formatBytes(MAX_FILE_SIZE_BYTES)} each
            </p>
          </div>
          <div className="rounded-3xl border border-line/70 bg-canvas/60 p-4 text-sm">
            <p className="text-muted">Accepted types</p>
            <p className="mt-2 font-medium">{tool.accept.join(", ")}</p>
          </div>
          <div className="rounded-3xl border border-line/70 bg-canvas/60 p-4 text-sm">
            <p className="text-muted">Queue insight</p>
            <p className="mt-2 font-medium">
              {typeof job?.meta.queue_position === "number" && job.meta.queue_position > 0
                ? `Position ${job.meta.queue_position}`
                : "Fair-share scheduling active"}
            </p>
          </div>
        </div>

        {selectedPreviewUrls.length > 0 ? (
          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {selectedPreviewUrls.slice(0, 2).map((previewUrl, index) => (
              <div key={previewUrl} className="overflow-hidden rounded-[24px] border border-line/70 bg-canvas/60">
                <div className="border-b border-line/70 px-4 py-3 text-sm font-medium">Input preview {index + 1}</div>
                <img src={previewUrl} alt={`Selected file ${index + 1}`} className="h-56 w-full object-cover" />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section className="space-y-6">
        <div className="rounded-[28px] border border-line/70 bg-panel/85 p-6 shadow-soft">
          <h2 className="text-lg font-semibold">Live status</h2>
          {!job ? (
            <div className="mt-4 rounded-3xl border border-dashed border-line/70 p-6 text-sm text-muted">
              {tool.available === false
                ? "This tool is paused while AI enhancement is being improved."
                : "Your latest job status and downloads will appear here."}
            </div>
          ) : (
            <div className="mt-4 space-y-4">
              <p className="text-sm text-muted">{statusMessage}</p>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium capitalize">{job.status}</span>
                <span className="text-sm text-muted">{job.progress}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-canvas">
                <div className="h-full rounded-full bg-brand transition-all" style={{ width: `${job.progress}%` }} />
              </div>
              <p className="text-sm text-muted">
                ETA {job.eta_seconds ? `~${job.eta_seconds}s` : "calculating"} | Job ID {job.id}
              </p>
              {tool.slug === "upscale" ? (
                <p className="text-sm text-muted">
                  Mode{" "}
                  {String(job.meta.quality_mode ?? qualityMode) === "high_quality"
                    ? "High Quality AI"
                    : "Standard AI"}
                  {job.outputs[0]?.meta.mode_message ? ` | ${job.outputs[0].meta.mode_message}` : ""}
                </p>
              ) : null}
              {typeof job.meta.attempt_count === "number" && Number(job.meta.attempt_count) > 0 ? (
                <p className="text-sm text-muted">
                  Retry attempt {job.meta.attempt_count} of {job.meta.max_retries ?? job.meta.attempt_count}
                </p>
              ) : null}
              {typeof job.meta.queue_position === "number" && job.meta.queue_position > 0 ? (
                <p className="text-sm text-muted">Waiting in queue at position {job.meta.queue_position}.</p>
              ) : null}
              {typeof job.meta.priority_score === "number" ? (
                <p className="text-sm text-muted">Queue fairness score: {job.meta.priority_score}.</p>
              ) : null}
              {zipOutput ? (
                <div className="rounded-2xl border border-brand/20 bg-brand.soft/60 p-4">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <div>
                      <p className="font-medium">Download all (ZIP)</p>
                      <p className="mt-1 text-xs text-muted">
                        {zipOutput.meta.file_count ?? 0} PDF files bundled into one archive.
                      </p>
                    </div>
                    <a
                      href={zipOutput.share_url ? resolveApiUrl(zipOutput.share_url) : getDownloadUrl(zipOutput.file_id)}
                      className="inline-flex items-center gap-2 rounded-full bg-foreground px-4 py-2 text-xs font-medium text-canvas transition hover:opacity-90"
                    >
                      Download ZIP
                    </a>
                  </div>
                </div>
              ) : null}
              {fileOutputs.map((output) => (
                <div key={output.file_id} className="rounded-2xl border border-line/70 bg-canvas/60 p-3">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <a
                      href={output.share_url ? resolveApiUrl(output.share_url) : getDownloadUrl(output.file_id)}
                      className="truncate font-medium transition hover:text-brand"
                    >
                      {output.filename}
                    </a>
                    <div className="flex items-center gap-2">
                      <span className="text-muted">{formatBytes(output.size_bytes)}</span>
                      <button
                        type="button"
                        onClick={() => copyShareLink(output.file_id)}
                        className="inline-flex items-center gap-1 rounded-full border border-line/70 px-2.5 py-1 text-xs transition hover:border-brand/40"
                      >
                        <Copy className="h-3 w-3" />
                        Copy link
                      </button>
                    </div>
                  </div>
                  {tool.slug === "pdf-split" ? (
                    <p className="mt-2 text-xs text-muted">
                      {output.meta.split_mode === "split_chunks" || output.meta.mode === "chunks"
                          ? `Chunk file ${output.meta.part_index ?? ""}`.trim()
                          : "Extracted PDF"}
                    </p>
                  ) : null}
                </div>
              ))}
              {latestImageOutput ? (
                <div className="overflow-hidden rounded-[24px] border border-line/70 bg-canvas/60">
                  <div className="border-b border-line/70 px-4 py-3 text-sm font-medium">Result preview</div>
                  <img
                    src={getDownloadUrl(latestImageOutput.file_id)}
                    alt={latestImageOutput.filename}
                    className="h-64 w-full object-contain bg-[radial-gradient(circle_at_center,rgba(148,163,184,0.16)_1px,transparent_1px)] [background-size:18px_18px]"
                  />
                </div>
              ) : null}
              {tool.slug === "compress" && compressionMeta ? (
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-2xl border border-line/70 bg-canvas/60 p-4 text-sm">
                    <p className="text-muted">Original</p>
                    <p className="mt-2 font-medium">{formatBytes(Number(compressionMeta.original_size ?? 0))}</p>
                  </div>
                  <div className="rounded-2xl border border-line/70 bg-canvas/60 p-4 text-sm">
                    <p className="text-muted">Compressed</p>
                    <p className="mt-2 font-medium">{formatBytes(Number(compressionMeta.compressed_size ?? 0))}</p>
                  </div>
                  <div className="rounded-2xl border border-line/70 bg-canvas/60 p-4 text-sm">
                    <p className="text-muted">Saved</p>
                    <p className="mt-2 font-medium">{compressionMeta.saved_percent ?? 0}%</p>
                  </div>
                </div>
              ) : null}
              {job.error ? (
                <div className="flex items-start gap-2 rounded-2xl border border-rose-500/20 bg-rose-500/10 p-4 text-sm text-rose-600 dark:text-rose-300">
                  <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
                  {job.error}
                </div>
              ) : null}
            </div>
          )}
        </div>

        <div className="rounded-[28px] border border-line/70 bg-panel/85 p-6 shadow-soft">
          <h2 className="text-lg font-semibold">Recent runs</h2>
          <div className="mt-4 space-y-3">
            {jobs.length === 0 ? (
              <p className="rounded-3xl border border-dashed border-line/70 p-6 text-sm text-muted">
                No runs for this tool yet. Start one job and CreatorLab will keep the latest statuses here.
              </p>
            ) : (
              jobs.slice(0, 5).map((item) => (
                <div key={item.id} className="rounded-2xl border border-line/70 bg-canvas/60 px-4 py-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="capitalize">{item.status}</span>
                    <span className="text-muted">{item.progress}%</span>
                  </div>
                  <p className="mt-1 truncate text-xs text-muted">{item.id}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
