import Link from "next/link";
import type { ReactNode } from "react";

import { Card, CardContent, ThemeToggle } from "@/components/ui";

type AuthLayoutProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
};

/** Centered auth screen shell (login / register). */
export function AuthLayout({ title, subtitle, children, footer }: AuthLayoutProps) {
  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <header className="border-b border-border bg-surface px-4 py-4">
        <div className="flex items-center justify-between gap-4">
          <Link href="/" className="text-lg font-semibold text-brand-700 hover:text-brand-800">
            CCSA
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <main className="flex flex-1 items-center justify-center px-4 py-10">
        <div className="w-full max-w-md">
          <div className="mb-6 text-center">
            <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
            {subtitle && <p className="mt-2 text-sm text-muted">{subtitle}</p>}
          </div>

          <Card>
            <CardContent className="space-y-4">{children}</CardContent>
          </Card>

          {footer && <div className="mt-6 text-center text-sm text-muted">{footer}</div>}
        </div>
      </main>
    </div>
  );
}
