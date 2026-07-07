import type { Metadata } from "next";
import Script from "next/script";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "CCSA — Credit Card Savings Analyzer",
  description:
    "Upload a card statement and see recurring charges, subscriptions, and estimated savings.",
};

/** Inline script applied before paint — mirrors `lib/theme/resolve.ts`. */
const themeInitScript = `
(function () {
  try {
    var stored = localStorage.getItem("ccsa_theme");
    var preference = stored === "light" || stored === "dark" || stored === "system" ? stored : "system";
    var resolved =
      preference === "system"
        ? window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light"
        : preference;
    document.documentElement.setAttribute("data-theme", resolved);
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-dvh bg-background text-foreground antialiased">
        <Script id="theme-init" strategy="beforeInteractive">
          {themeInitScript}
        </Script>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
