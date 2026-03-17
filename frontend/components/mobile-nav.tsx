"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Menu, X } from "lucide-react";
import { toast } from "sonner";
import { logOut } from "@/lib/api";
import { AuthSessionResponse } from "@/lib/types";

type NavItem = {
  href: string;
  label: string;
};

export function MobileNav({
  navItems,
  initialSession
}: {
  navItems: NavItem[];
  initialSession: AuthSessionResponse | null;
}) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [session, setSession] = useState<AuthSessionResponse | null>(initialSession);

  useEffect(() => {
    setSession(initialSession);
  }, [initialSession]);

  useEffect(() => {
    document.body.style.overflow = isOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  async function handleLogout() {
    try {
      await logOut();
      setSession(null);
      setIsOpen(false);
      toast.success("Signed out.");
      router.push("/");
      router.refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not sign out.");
    }
  }

  return (
    <div className="md:hidden">
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="inline-flex rounded-full border border-line/70 p-2"
        aria-label="Open navigation"
      >
        <Menu className="h-5 w-5" />
      </button>

      {isOpen ? (
        <div className="fixed inset-0 z-50 bg-slate-950/35 backdrop-blur-sm">
          <div className="ml-auto flex h-full w-[86vw] max-w-sm flex-col border-l border-line/70 bg-canvas p-6 shadow-soft">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold">CreatorLab</p>
                <p className="text-xs text-muted">Smart creator workspace</p>
              </div>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="inline-flex rounded-full border border-line/70 p-2"
                aria-label="Close navigation"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <nav className="mt-8 space-y-2">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsOpen(false)}
                  className="block rounded-2xl border border-line/70 bg-panel/85 px-4 py-3 text-sm font-medium"
                >
                  {item.label}
                </Link>
              ))}
            </nav>

            <div className="mt-8 rounded-[28px] border border-line/70 bg-panel/85 p-5">
              {session ? (
                <div className="space-y-3">
                  <p className="text-sm font-medium">{session.user.full_name || session.user.email}</p>
                  <p className="text-xs text-muted">
                    {session.usage.jobs_used} of {session.usage.jobs_limit ?? "unlimited"} jobs used this month
                  </p>
                  {!session.user.email_verified ? (
                    <Link
                      href={`/verify-email?email=${encodeURIComponent(session.user.email)}`}
                      onClick={() => setIsOpen(false)}
                      className="block rounded-full border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-center text-sm font-medium text-amber-700 dark:text-amber-300"
                    >
                      Verify email
                    </Link>
                  ) : null}
                  <Link
                    href="/dashboard"
                    onClick={() => setIsOpen(false)}
                    className="block rounded-full bg-foreground px-4 py-3 text-center text-sm font-medium text-canvas"
                  >
                    Dashboard
                  </Link>
                  <Link
                    href="/account"
                    onClick={() => setIsOpen(false)}
                    className="block rounded-full border border-line/70 px-4 py-3 text-center text-sm font-medium"
                  >
                    Account
                  </Link>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="block w-full rounded-full border border-line/70 px-4 py-3 text-sm font-medium"
                  >
                    Log out
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm text-muted">Use the tools right away. Accounts stay optional and only add higher limits and cross-device history later.</p>
                  <Link
                    href="/tools"
                    onClick={() => setIsOpen(false)}
                    className="block rounded-full border border-line/70 px-4 py-3 text-center text-sm font-medium"
                  >
                    Open tools
                  </Link>
                  <Link
                    href="/account"
                    onClick={() => setIsOpen(false)}
                    className="block rounded-full bg-foreground px-4 py-3 text-center text-sm font-medium text-canvas"
                  >
                    Optional account
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
