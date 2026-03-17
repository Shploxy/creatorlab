import { ResetPasswordForm } from "@/components/reset-password-form";

export default async function ResetPasswordPage({
  searchParams
}: {
  searchParams: Promise<{ token?: string }>;
}) {
  const params = await searchParams;

  return (
    <div className="mx-auto grid max-w-6xl gap-8 px-4 py-14 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8">
      <section className="rounded-[32px] border border-line/70 bg-panel/85 p-8 shadow-soft">
        <p className="text-sm uppercase tracking-[0.24em] text-brand">Reset password</p>
        <h2 className="mt-4 text-4xl font-semibold tracking-tight">Choose a new password and get back to work.</h2>
        <p className="mt-4 text-base leading-7 text-muted">
          Reset links are time-limited and stored securely, so the same flow works for local testing now and a real public deployment later.
        </p>
      </section>

      <ResetPasswordForm token={params.token} />
    </div>
  );
}
