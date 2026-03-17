import Link from "next/link";

export default function ToolNotFound() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-20 text-center sm:px-6 lg:px-8">
      <div className="rounded-[32px] border border-line/70 bg-panel/85 p-10 shadow-soft">
        <p className="text-sm uppercase tracking-[0.24em] text-brand">Tool not found</p>
        <h1 className="mt-4 text-3xl font-semibold">That workflow is not available yet.</h1>
        <p className="mt-4 text-base leading-7 text-muted">
          Head back to the tools overview to launch one of the CreatorLab utilities included in version 1.
        </p>
        <Link href="/tools" className="mt-8 inline-flex rounded-full bg-foreground px-5 py-3 text-sm font-medium text-canvas">
          Browse tools
        </Link>
      </div>
    </div>
  );
}
