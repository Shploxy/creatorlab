const faqs = [
  {
    question: "Is CreatorLab using real AI models already?",
    answer:
      "Version 1 uses production-shaped service modules. Image upscaling is a placeholder implementation, and background removal is rembg-ready with a local fallback path."
  },
  {
    question: "Can this run on a Windows PC first?",
    answer:
      "Yes. The repo is designed for local frontend and backend development on Windows, with optional Docker support later."
  },
  {
    question: "Where are processed files stored?",
    answer:
      "Outputs are written into a local backend storage folder and exposed through download endpoints. The storage layer is structured so cloud storage can be added later."
  },
  {
    question: "Does it support auth?",
    answer:
      "The app is auth-ready in structure, but version 1 runs in local demo mode to keep setup simple."
  }
];

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
        <p className="text-sm uppercase tracking-[0.24em] text-brand">About CreatorLab</p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight">A practical creator utility platform with room to grow.</h1>
        <p className="mt-5 text-base leading-8 text-muted">
          CreatorLab is meant to feel like a serious product from the start: clear tool pages, a modern dashboard, queue-aware backend APIs, local output management, and a modular architecture that makes future AI upgrades straightforward.
        </p>
      </section>

      <section className="mt-8 grid gap-4">
        {faqs.map((faq) => (
          <article key={faq.question} className="rounded-[28px] border border-line/70 bg-panel/85 p-6 shadow-soft">
            <h2 className="text-lg font-semibold">{faq.question}</h2>
            <p className="mt-3 text-sm leading-7 text-muted">{faq.answer}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
