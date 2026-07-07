"use client";

import Link from "next/link";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { ArchivedList } from "@/components/dashboard/ArchivedList";
import { AppShell } from "@/components/layout/AppShell";

export default function ArchivedPage() {
  return (
    <RequireAuth>
      <AppShell>
        <div className="space-y-6">
          <div>
            <Link
              href="/dashboard"
              className="text-sm font-medium text-muted transition-colors hover:text-foreground"
            >
              ← Back to dashboard
            </Link>
            <h1 className="mt-2 text-2xl font-semibold text-foreground">Archived</h1>
            <p className="mt-1 text-muted">
              Hidden statements kept for your records. Restore them or delete them permanently.
            </p>
          </div>
          <ArchivedList />
        </div>
      </AppShell>
    </RequireAuth>
  );
}
