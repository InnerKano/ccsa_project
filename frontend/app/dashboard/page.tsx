"use client";

import { Suspense } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Spinner } from "@/components/ui";

import { DashboardContent } from "./DashboardContent";

export default function DashboardPage() {
  return (
    <RequireAuth>
      <AppShell>
        <Suspense
          fallback={
            <div className="flex justify-center py-16">
              <Spinner size={32} />
            </div>
          }
        >
          <DashboardContent />
        </Suspense>
      </AppShell>
    </RequireAuth>
  );
}
