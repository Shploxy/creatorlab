import Link from "next/link";

export function HistoryFilters({
  page,
  total,
  pageSize,
  status,
  tool,
  search
}: {
  page: number;
  total: number;
  pageSize: number;
  status?: string;
  tool?: string;
  search?: string;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  function buildHref(nextPage: number, nextStatus = status, nextTool = tool) {
    const params = new URLSearchParams();
    params.set("page", String(nextPage));
    if (nextStatus) params.set("status", nextStatus);
    if (nextTool) params.set("tool", nextTool);
    if (search) params.set("search", search);
    return `/history?${params.toString()}`;
  }

  return (
    <div className="rounded-[28px] border border-line/70 bg-panel/85 p-6 shadow-soft">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <form action="/history" className="grid gap-4 md:grid-cols-3 lg:flex lg:flex-1">
          <label className="block">
            <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-muted">Search</span>
            <input
              name="search"
              defaultValue={search}
              placeholder="Job ID or filename"
              className="w-full rounded-2xl border border-line/70 bg-canvas px-4 py-3 text-sm outline-none transition focus:border-brand/40"
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-muted">Status</span>
            <select
              name="status"
              defaultValue={status ?? ""}
              className="w-full rounded-2xl border border-line/70 bg-canvas px-4 py-3 text-sm outline-none transition focus:border-brand/40"
            >
              <option value="">All statuses</option>
              <option value="queued">Queued</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </label>
          <label className="block">
            <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-muted">Tool</span>
            <select
              name="tool"
              defaultValue={tool ?? ""}
              className="w-full rounded-2xl border border-line/70 bg-canvas px-4 py-3 text-sm outline-none transition focus:border-brand/40"
            >
              <option value="">All tools</option>
              <option value="upscale">Upscale</option>
              <option value="background-remove">Background remove</option>
              <option value="compress">Compress</option>
              <option value="pdf-merge">PDF merge</option>
              <option value="pdf-split">PDF split</option>
              <option value="images-to-pdf">Images to PDF</option>
            </select>
          </label>
          <input type="hidden" name="page" value="1" />
          <button
            type="submit"
            className="rounded-full bg-foreground px-5 py-3 text-sm font-medium text-canvas transition hover:opacity-90 lg:self-end"
          >
            Apply filters
          </button>
        </form>

        <div className="flex items-center gap-3">
          <Link
            href={buildHref(Math.max(page - 1, 1))}
            className={`rounded-full border border-line/70 px-4 py-2 text-sm ${page <= 1 ? "pointer-events-none opacity-50" : ""}`}
          >
            Previous
          </Link>
          <span className="text-sm text-muted">
            Page {page} of {totalPages}
          </span>
          <Link
            href={buildHref(Math.min(page + 1, totalPages))}
            className={`rounded-full border border-line/70 px-4 py-2 text-sm ${page >= totalPages ? "pointer-events-none opacity-50" : ""}`}
          >
            Next
          </Link>
        </div>
      </div>
    </div>
  );
}
