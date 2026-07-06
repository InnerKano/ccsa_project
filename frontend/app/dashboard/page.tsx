"use client";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent, CardTitle } from "@/components/ui";

/**
 * Dashboard hub — A4.4 adds statement list + run analysis.
 * A4.2 ships the protected shell and routing so auth → dashboard is verifiable.
 */
export default function DashboardPage() {
  return (
    <RequireAuth>
      <AppShell>
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Dashboard</h1>
            <p className="mt-1 text-muted">
              Your statements and savings analysis will appear here.
            </p>
          </div>

          <Card>
            <CardContent>
              <CardTitle>Next up</CardTitle>
              <p className="mt-2 text-sm text-muted">
                Upload a CSV statement to start detecting subscriptions and estimated savings.
              </p>
            </CardContent>
          </Card>
        </div>
      </AppShell>
    </RequireAuth>
  );
}
