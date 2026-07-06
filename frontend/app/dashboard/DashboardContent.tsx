"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Alert, buttonClass, Card, CardContent, CardTitle } from "@/components/ui";

/**
 * Dashboard hub — A4.4 adds statement list + run analysis.
 * A4.3 adds upload success feedback via ?uploaded=&count= query params.
 */
export function DashboardContent() {
  const searchParams = useSearchParams();
  const uploadedId = searchParams.get("uploaded");
  const transactionCount = searchParams.get("count");

  const [showSuccess, setShowSuccess] = useState(Boolean(uploadedId));

  useEffect(() => {
    setShowSuccess(Boolean(uploadedId));
  }, [uploadedId]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Dashboard</h1>
        <p className="mt-1 text-muted">
          Your statements and savings analysis will appear here.
        </p>
      </div>

      {showSuccess && uploadedId && (
        <Alert variant="success">
          Statement uploaded successfully
          {transactionCount
            ? ` — ${transactionCount} transaction${transactionCount === "1" ? "" : "s"} parsed.`
            : "."}
          <button
            type="button"
            className="ml-2 text-sm font-medium underline"
            onClick={() => setShowSuccess(false)}
          >
            Dismiss
          </button>
        </Alert>
      )}

      <Card>
        <CardContent>
          <CardTitle>Get started</CardTitle>
          <p className="mt-2 text-sm text-muted">
            Upload a CSV statement to start detecting subscriptions and estimated savings.
          </p>
          <Link href="/upload" className={`${buttonClass("primary")} mt-4 inline-flex`}>
            Upload statement
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
