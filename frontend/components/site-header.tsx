import Link from "next/link";
import { FlaskConical } from "lucide-react";
import { AuthStatus } from "@/components/auth-status";
import { MobileNav } from "@/components/mobile-nav";
import { ThemeToggle } from "@/components/theme-toggle";
import { AuthSessionResponse } from "@/lib/types";

const navItems = [
  { href: "/tools", label: "Tools" },
  { href: "/dashboard", label: "Recent jobs" },
  { href: "/history", label: "History" },
  { href: "/pricing", label: "Pricing" },
  { href: "/about", label: "About" }
];

export function SiteHeader({ initialSession }: { initialSession: AuthSessionResponse | null }) {
  return (
    <header className="sticky top-0 z-40 border-b border-line/60 bg-canvas/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-3 text-sm font-semibold tracking-wide">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand text-white shadow-soft">
            <FlaskConical className="h-5 w-5" />
          </span>
          <span>
            CreatorLab
            <span className="block text-xs font-normal text-muted">All your creator tools in one smart workspace.</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-6 md:flex">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} className="text-sm text-muted transition hover:text-foreground">
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <AuthStatus initialSession={initialSession} />
          <Link href="/tools" className="hidden rounded-full bg-foreground px-4 py-2 text-sm font-medium text-canvas transition hover:opacity-90 lg:inline-flex">
            Use tools now
          </Link>
          <MobileNav navItems={navItems} initialSession={initialSession} />
        </div>
      </div>
    </header>
  );
}
