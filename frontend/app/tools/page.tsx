import { SectionHeading } from "@/components/section-heading";
import { ToolCard } from "@/components/tool-card";
import { toolDefinitions } from "@/lib/tools";

export default function ToolsPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <SectionHeading
        eyebrow="Workspace"
        title="Open a tool and get to work"
        description="No signup required. Pick the job you need, upload a file, and download the result with the same fast flow across every tool."
      />
      <div className="mt-10 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {toolDefinitions.map((tool) => (
          <ToolCard key={tool.slug} slug={tool.slug} />
        ))}
      </div>
    </div>
  );
}
