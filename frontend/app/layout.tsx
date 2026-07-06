import type { Metadata } from "next";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "CCSA — Credit Card Savings Analyzer",
  description:
    "Upload a card statement and see recurring charges, subscriptions, and estimated savings.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-dvh bg-background text-foreground antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
