export default function ToolLoading() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="h-[520px] animate-pulse rounded-[28px] border border-line/70 bg-panel/70" />
        <div className="space-y-6">
          <div className="h-64 animate-pulse rounded-[28px] border border-line/70 bg-panel/70" />
          <div className="h-56 animate-pulse rounded-[28px] border border-line/70 bg-panel/70" />
        </div>
      </div>
    </div>
  );
}
