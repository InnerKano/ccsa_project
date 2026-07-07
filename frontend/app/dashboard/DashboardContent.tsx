"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { mutate } from "swr";

import { StatementList } from "@/components/dashboard/StatementList";
import { Alert, buttonClass, Card, CardContent, CardTitle } from "@/components/ui";

/**
 * Dashboard hub — lists statements, runs analysis, links to saved results.
 */
export function DashboardContent() {
  const searchParams = useSearchParams();
  const uploadedId = searchParams.get("uploaded");
  const transactionCount = searchParams.get("count");

  const [showUploadSuccess, setShowUploadSuccess] = useState(Boolean(uploadedId));

  useEffect(() => {
    setShowUploadSuccess(Boolean(uploadedId));
    if (uploadedId) {
      void mutate("statements");
      void mutate("analyses");
    }
  }, [uploadedId]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Dashboard</h1>
          <p className="mt-1 text-muted">
            Your uploaded statements and savings analyses.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Link href="/dashboard/archived" className={`${buttonClass("secondary")} inline-flex`}>
            Archived
          </Link>
          <Link href="/upload" className={`${buttonClass("primary")} inline-flex`}>
            Upload statement
          </Link>
        </div>
      </div>

      {showUploadSuccess && uploadedId && (
        <Alert variant="success">
          Statement uploaded successfully
          {transactionCount
            ? ` — ${transactionCount} transaction${transactionCount === "1" ? "" : "s"} parsed.`
            : "."}
          <button
            type="button"
            className="ml-2 text-sm font-medium underline"
            onClick={() => setShowUploadSuccess(false)}
          >
            Dismiss
          </button>
        </Alert>
      )}

      <StatementList />
    </div>
  );
}
