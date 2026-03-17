import Link from "next/link";
import { ArrowRight, BadgeCheck, Clock3, FolderKanban, ShieldCheck, Sparkles, Users2, Zap } from "lucide-react";
import { SectionHeading } from "@/components/section-heading";
import { ToolCard } from "@/components/tool-card";
import { toolDefinitions } from "@/lib/tools";

const featureItems = [
  {
    title: "One workspace, multiple creator tools",
    description: "Run image and PDF tasks in one place with consistent uploads, progress feedback, and fast downloads.",
    icon: FolderKanban
  },
  {
    title: "No signup required",
    description: "Open the site and use the tools immediately. CreatorLab remembers recent work on the same device without forcing an account.",
    icon: ShieldCheck
  },
  {
    title: "Fast turnaround on repetitive tasks",
    description: "Use recent history, saved downloads, and a cleaner queue flow to spend less time on repetitive cleanup.",
    icon: Clock3
  }
];

const pricingStyle = [
  "Use the core tools right away on the free tier",
  "Recent jobs stay visible on the same device",
  "No watermark and no intrusive ads",
  "Optional paid upgrade only for heavier use and convenience"
];

const audienceGroups = [
  {
    title: "Freelancers",
    description: "Clean up client assets, compress deliverables, and keep every export easy to find."
  },
  {
    title: "Students",
    description: "Merge class PDFs, convert screenshots into reports, and save time on repetitive prep work."
  },
  {
    title: "Small teams",
    description: "Standardize file processing in one shared workspace that can move from local to cloud."
  }
];

export default function HomePage() {
  return (
    <div>
      <section className="mx-auto grid max-w-7xl gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[1.2fr_0.8fr] lg:px-8 lg:py-24">
        <div>
          <div className="inline-flex rounded-full border border-line/70 bg-panel/80 px-4 py-2 text-sm text-muted shadow-soft">
            CreatorLab | Fast creator tools. No signup required.
          </div>
          <h1 className="mt-8 max-w-4xl text-5xl font-semibold tracking-tight sm:text-6xl">
            Fast, useful creator tools you can use immediately.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-muted">
            Upscale images, remove backgrounds, compress files, and handle PDF work in one clean workspace. No forced login, no watermark, and no spammy flow.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href="/tools"
              className="inline-flex items-center gap-2 rounded-full bg-foreground px-6 py-3 text-sm font-medium text-canvas transition hover:opacity-90"
            >
              Use tools now
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-full border border-line/70 bg-panel/85 px-6 py-3 text-sm font-medium transition hover:border-brand/40"
            >
              Recent jobs
            </Link>
            <Link href="/pricing" className="inline-flex items-center gap-2 rounded-full px-2 py-3 text-sm font-medium text-muted transition hover:text-foreground">
              Pricing
            </Link>
          </div>
          <div className="mt-10 grid gap-4 sm:grid-cols-3">
            {[
              ["6", "creator tools"],
              ["50/mo", "free jobs per device"],
              ["0", "required signups"]
            ].map(([value, label]) => (
              <div key={label} className="rounded-[24px] border border-line/70 bg-panel/80 p-5 shadow-soft">
                <p className="text-3xl font-semibold">{value}</p>
                <p className="mt-2 text-sm text-muted">{label}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[32px] border border-line/70 bg-panel/80 p-6 shadow-soft">
          <div className="rounded-[28px] bg-[#03131f] p-6 text-white">
            <div className="flex items-center justify-between text-sm text-white/70">
              <span>Workspace pulse</span>
              <span className="inline-flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-emerald-300" />
                instant utility
              </span>
            </div>
            <div className="mt-8 grid gap-4">
              {[
                ["AI Upscaler", "Fast default AI mode with optional high-quality path", "No signup"],
                ["Background Removal", "u2net via rembg with PNG exports", "Transparent output"],
                ["PDF Toolkit", "Merge, split, convert", "Simple workflow"]
              ].map(([title, text, meta]) => (
                <div key={title} className="rounded-[24px] border border-white/10 bg-white/5 p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">{title}</h3>
                    <Zap className="h-4 w-4 text-amber-300" />
                  </div>
                  <p className="mt-3 text-sm text-white/70">{text}</p>
                  <p className="mt-2 text-xs uppercase tracking-[0.22em] text-white/45">{meta}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Platform"
          title="Useful tools that feel like one product, not a pile of utilities"
          description="Every workflow follows the same rhythm: upload, process, download, and return later on the same device without being forced through account setup."
        />
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {featureItems.map((feature) => (
            <div key={feature.title} className="rounded-[28px] border border-line/70 bg-panel/85 p-6 shadow-soft">
              <feature.icon className="h-6 w-6 text-brand" />
              <h3 className="mt-5 text-xl font-semibold">{feature.title}</h3>
              <p className="mt-3 text-sm leading-6 text-muted">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Who It Helps"
          title="Built for the people doing real file work every week"
          description="CreatorLab is designed for practical workflows, not novelty demos. It gives creators and operators one reliable place to run common jobs fast."
        />
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {audienceGroups.map((group) => (
            <div key={group.title} className="rounded-[28px] border border-line/70 bg-panel/85 p-6 shadow-soft">
              <Users2 className="h-6 w-6 text-brand" />
              <h3 className="mt-5 text-xl font-semibold">{group.title}</h3>
              <p className="mt-3 text-sm leading-6 text-muted">{group.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Toolset"
          title="Version 1 includes six practical creator utilities"
          description="Image and PDF jobs are organized into clear cards so the workspace feels fast to learn, pleasant to use, and easy to expand."
        />
        <div className="mt-10 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {toolDefinitions.map((tool) => (
            <ToolCard key={tool.slug} slug={tool.slug} />
          ))}
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8">
        <div className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
          <SectionHeading
          eyebrow="Plans"
          title="Free first. Upgrade only when it saves you time."
          description="The free tier is meant to do real work. Paid plans are there for heavier use, faster queues, and convenience, not to block the basics."
        />
          <div className="mt-8 grid gap-4">
            {pricingStyle.map((item) => (
              <div key={item} className="rounded-3xl border border-line/70 bg-canvas/60 px-4 py-4 text-sm">
                {item}
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[32px] border border-brand/20 bg-brand px-8 py-10 text-white shadow-soft">
          <p className="text-sm uppercase tracking-[0.24em] text-white/70">Why it feels different</p>
          <h2 className="mt-4 text-3xl font-semibold">Built to feel clean, fast, and respectful.</h2>
          <p className="mt-4 text-base leading-7 text-white/80">
            CreatorLab is designed like a utility product first: no intrusive ads, no watermark, and no account wall before someone gets value.
          </p>
          <div className="mt-8 space-y-3 text-sm text-white/80">
            {[
              "Recent jobs remembered on the same device",
              "Optional accounts only when they add value",
              "Simple free tier with fair limits"
            ].map((item) => (
              <div key={item} className="flex items-center gap-2">
                <BadgeCheck className="h-4 w-4 shrink-0" />
                <span>{item}</span>
              </div>
            ))}
          </div>
          <Link
            href="/tools"
            className="mt-8 inline-flex items-center gap-2 rounded-full bg-white px-5 py-3 text-sm font-medium text-brand transition hover:opacity-90"
          >
            Open the tools
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
