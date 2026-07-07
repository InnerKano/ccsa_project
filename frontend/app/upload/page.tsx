"use client";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { StatementUploadForm } from "@/components/statements/StatementUploadForm";
import { Card, CardContent, CardTitle } from "@/components/ui";

export default function UploadPage() {
  return (
    <RequireAuth>
      <AppShell>
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Upload statement</h1>
            <p className="mt-1 text-muted">
              Import a CSV/TSV/TXT export or a bank statement PDF. We parse it in memory and save
              only the transactions needed for analysis.
            </p>
          </div>

          <Card>
            <CardContent>
              <CardTitle>Statement file</CardTitle>
              <div className="mt-4">
                <StatementUploadForm />
              </div>
            </CardContent>
          </Card>
        </div>
      </AppShell>
    </RequireAuth>
  );
}
