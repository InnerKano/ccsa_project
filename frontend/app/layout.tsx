import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "CCSA",
  description: "Credit Card Savings Analyzer",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
