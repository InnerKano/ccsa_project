"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import useSWR from "swr";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Alert, buttonClass, Card, CardContent, Spinner } from "@/components/ui";
import { getAnalysis } from "@/lib/api/analysis";
import { formatCurrency, formatDate } from "@/lib/format";

/**
 * Analysis results — headline metrics (A4.4). Subscription breakdown and
 * recommendations are extended in A4.5 on this same route.
 */
function AnalysisContent() {
  const params = useParams();
  const analysisId = typeof params.id === "string" ? params.id : "";

  const { data, error, isLoading } = useSWR(
    analysisId ? `analysis-${analysisId}` : null,
    () => getAnalysis(analysisId),
  );

  if (isLoading) {
    return (
      <div className="flex justify-center py-16" role="status" aria-label="Loading analysis">
        <Spinner size={32} />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="error">
        {error instanceof Error ? error.message : "Could not load analysis"}
      </Alert>
    );
  }

  if (!data) {
    return <Alert variant="info">Analysis not found.</Alert>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Analysis results</h1>
        <p className="mt-1 text-sm text-muted">
          Rules-based scan · {formatDate(data.created_at)}
          {!data.ai_enabled && " · AI enrichment off"}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardContent>
            <p className="text-sm text-muted">Monthly recurring total</p>
            <p className="mt-1 text-2xl font-semibold text-foreground">
              {formatCurrency(data.monthly_recurring_total)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <p className="text-sm text-muted">Estimated savings</p>
            <p className="mt-1 text-2xl font-semibold text-brand-700">
              {formatCurrency(data.estimated_savings)}
            </p>
          </CardContent>
        </Card>
      </div>

      <Link href="/dashboard" className={buttonClass("secondary")}>
        Back to dashboard
      </Link>
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <RequireAuth>
      <AppShell>
        <AnalysisContent />
      </AppShell>
    </RequireAuth>
  );
}
