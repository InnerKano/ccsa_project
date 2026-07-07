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

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-4 py-20 text-center sm:py-28">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted sm:text-sm">
          Credit Card Savings Analyzer
        </p>

        <h1 className="mt-4 max-w-2xl text-4xl font-bold leading-[1.1] tracking-tight text-foreground sm:mt-5 sm:text-5xl sm:leading-[1.08] lg:text-6xl">
          See where your
          <br />
          recurring <span className="text-brand-700">money</span> goes
        </h1>

        <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted sm:mt-8">
          Upload a card statement (CSV/TSV/TXT or PDF). We detect subscriptions and recurring
          charges, then estimate how much you could save — no spreadsheet required.
        </p>

        <div className="mt-8 flex flex-wrap justify-center gap-4 sm:mt-10">
          <Link href="/register" className={buttonClass("primary")}>
            Get started
          </Link>
          <Link href="/login" className={buttonClass("secondary")}>
            Sign in
          </Link>
        </div>

        <p className="mt-10 max-w-xl text-sm text-muted sm:mt-12">
          Your raw file is never stored — only normalized transactions needed for analysis.
        </p>
      </main>
    </div>
  );
}
