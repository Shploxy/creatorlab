import { fetchJobsPage } from "@/lib/api";
import { HistoryFilters } from "@/components/history-filters";
import { JobHistory } from "@/components/job-history";
import { PaginatedJobs } from "@/lib/types";

export default async function HistoryPage({
  searchParams
}: {
  searchParams: Promise<{ page?: string; status?: string; tool?: string; search?: string }>;
}) {
  const params = await searchParams;
  const page = Number(params.page ?? "1") || 1;
  let result: PaginatedJobs = { items: [], total: 0, page, page_size: 10 };
  try {
    result = await fetchJobsPage({
      page,
      pageSize: 10,
      status: params.status,
      tool: params.tool,
      search: params.search
    });
  } catch {
    result = { items: [], total: 0, page, page_size: 10 };
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
        <p className="text-sm uppercase tracking-[0.24em] text-brand">History</p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight">Your device history</h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-muted">
          CreatorLab keeps recent jobs tied to this device, so you can come back later, reopen downloads, and continue where you left off without signing up.
        </p>
      </section>

      <div className="mt-8">
        <HistoryFilters
          page={result.page}
          total={result.total}
          pageSize={result.page_size}
          status={params.status}
          tool={params.tool}
          search={params.search}
        />
      </div>

      <div className="mt-8">
        <JobHistory jobs={result.items} title={`Recent jobs on this device (${result.total})`} />
      </div>
    </div>
  );
}
