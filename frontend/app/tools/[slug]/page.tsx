import { notFound } from "next/navigation";
import { fetchJobs } from "@/lib/api";
import { JobRecord } from "@/lib/types";
import { getToolDefinition } from "@/lib/tools";
import { ToolWorkbench } from "@/components/tool-workbench";

export default async function ToolPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const tool = getToolDefinition(slug);
  if (!tool) notFound();

  let jobs: JobRecord[] = [];
  try {
    jobs = (await fetchJobs()).filter((job) => job.tool === slug);
  } catch {
    jobs = [];
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <ToolWorkbench tool={tool} initialJobs={jobs} />
    </div>
  );
}
