import Link from "next/link";
import { ArrowUpRight, Clock3 } from "lucide-react";
import { getToolDefinition, toolIcons } from "@/lib/tools";

export function ToolCard({ slug }: { slug: string }) {
  const tool = getToolDefinition(slug);
  if (!tool) return null;
  const Icon = toolIcons[tool.slug];

  if (tool.available === false) {
    return (
      <div className="rounded-[28px] border border-line/70 bg-panel/85 p-6 shadow-soft">
        <div className="mb-5 flex items-center justify-between">
          <span className="inline-flex rounded-full bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-700 dark:text-amber-300">
            {tool.availabilityLabel ?? "Coming soon"}
          </span>
          <Clock3 className="h-5 w-5 text-muted" />
        </div>
        <h3 className="text-lg font-semibold">{tool.title}</h3>
        <p className="mt-3 text-sm leading-6 text-muted">{tool.description}</p>
        <div className="mt-6 flex items-center justify-between text-sm">
          <span className="text-muted">{tool.eta}</span>
          <span className="inline-flex items-center gap-1 font-medium text-muted">
            AI enhancement in progress
          </span>
        </div>
      </div>
    );
  }

  return (
    <Link
      href={`/tools/${tool.slug}`}
      className="group rounded-[28px] border border-line/70 bg-panel/85 p-6 shadow-soft transition hover:-translate-y-1 hover:border-brand/40"
    >
      <div className="mb-5 flex items-center justify-between">
        <span className="inline-flex rounded-full bg-brand.soft px-3 py-1 text-xs font-medium text-brand">{tool.badge}</span>
        <Icon className="h-5 w-5 text-muted transition group-hover:text-brand" />
      </div>
      <h3 className="text-lg font-semibold">{tool.title}</h3>
      <p className="mt-3 text-sm leading-6 text-muted">{tool.description}</p>
      <div className="mt-6 flex items-center justify-between text-sm">
        <span className="text-muted">{tool.eta} | no signup</span>
        <span className="inline-flex items-center gap-1 font-medium text-foreground">
          Launch tool
          <ArrowUpRight className="h-4 w-4" />
        </span>
      </div>
    </Link>
  );
}
