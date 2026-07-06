"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { Button } from "@/components/ui";
import { cn } from "@/lib/cn";
import { useAuth } from "@/lib/auth/context";

type NavItem = {
  href: string;
  label: string;
};

const NAV_ITEMS: NavItem[] = [{ href: "/dashboard", label: "Dashboard" }];

type AppShellProps = {
  children: ReactNode;
};

/** Authenticated app chrome — header nav + main content area. */
export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { logout } = useAuth();

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between gap-4 px-4">
          <Link href="/dashboard" className="shrink-0 text-lg font-semibold text-brand-700">
            CCSA
          </Link>

          <nav className="flex items-center gap-1" aria-label="Main">
            {NAV_ITEMS.map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    active
                      ? "bg-brand-50 text-brand-800"
                      : "text-muted hover:bg-surface-muted hover:text-foreground",
                  )}
                  aria-current={active ? "page" : undefined}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <Button type="button" variant="ghost" size="sm" onClick={handleLogout}>
            Sign out
          </Button>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">{children}</main>
    </div>
  );
}
