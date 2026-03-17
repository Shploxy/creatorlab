import type { Metadata } from "next";
import { Manrope } from "next/font/google";
import "@/app/globals.css";
import { Providers } from "@/components/providers";
import { SiteHeader } from "@/components/site-header";
import { SiteFooter } from "@/components/site-footer";
import { fetchCurrentUser } from "@/lib/api";

const manrope = Manrope({
  subsets: ["latin"]
});

export const metadata: Metadata = {
  title: "CreatorLab",
  description: "All your creator tools in one smart workspace."
};

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const session = await fetchCurrentUser().catch(() => null);

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={manrope.className} suppressHydrationWarning>
        <Providers>
          <div className="relative min-h-screen">
            <SiteHeader initialSession={session} />
            <main>{children}</main>
            <SiteFooter />
          </div>
        </Providers>
      </body>
    </html>
  );
}
