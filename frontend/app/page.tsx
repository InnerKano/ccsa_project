"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { buttonClass, Spinner, ThemeToggle } from "@/components/ui";
import { useAuth } from "@/lib/auth/context";

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner size={32} />
      </div>
    );
  }

  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <header className="border-b border-border bg-surface px-4 py-4">
        <div className="flex items-center justify-between gap-4">
          <span className="text-lg font-semibold text-brand-700">CCSA</span>
          <ThemeToggle />
        </div>
      </header>

      <main className="mx-auto flex max-w-2xl flex-1 flex-col justify-center px-4 py-16">
        <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          See where your recurring money goes
        </h1>
        <p className="mt-4 text-lg text-muted">
          Upload a card statement (CSV/TSV/TXT or PDF). We detect subscriptions and recurring
          charges, then estimate how much you could save — no spreadsheet required.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/register" className={buttonClass("primary")}>
            Get started
          </Link>
          <Link href="/login" className={buttonClass("secondary")}>
            Sign in
          </Link>
        </div>
        <p className="mt-10 text-sm text-muted">
          Your raw file is never stored — only normalized transactions needed for analysis.
        </p>
      </main>
    </div>
  );
}
