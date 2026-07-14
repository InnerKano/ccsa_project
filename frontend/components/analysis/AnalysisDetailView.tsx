"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";

import { AnalysisSummaryCards } from "@/components/analysis/AnalysisSummaryCards";
import { RecommendationList } from "@/components/analysis/RecommendationList";
import { SpendingComparisonCard } from "@/components/analysis/SpendingComparisonCard";
import { SubscriptionList } from "@/components/analysis/SubscriptionList";
import { Alert, Button, buttonClass, Spinner } from "@/components/ui";
import { exportAnalysisCsv } from "@/lib/api/exportAnalysisCsv";
import { getAnalysis } from "@/lib/api/analysis";
import { getStatement } from "@/lib/api/statements";
import { formatDate } from "@/lib/format";

type AnalysisDetailViewProps = {
  analysisId: string;
};

export function AnalysisDetailView({ analysisId }: AnalysisDetailViewProps) {
  const {
    data: analysis,
    error: analysisError,
    isLoading: analysisLoading,
  } = useSWR(analysisId ? `analysis-${analysisId}` : null, () => getAnalysis(analysisId));

  const statementId = analysis?.statement_id;
  const { data: statement } = useSWR(
    statementId ? `statement-meta-${statementId}` : null,
    () => getStatement(statementId!),
  );

  const currency = statement?.currency ?? "USD";

  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  async function handleExport() {
    setExporting(true);
    setExportError(null);
    try {
      await exportAnalysisCsv(analysisId);
    } catch (error) {
      setExportError(error instanceof Error ? error.message : "Failed to export analysis");
    } finally {
      setExporting(false);
    }
  }

  if (analysisLoading) {
    return (
      <div className="flex justify-center py-16" role="status" aria-label="Loading analysis">
        <Spinner size={32} />
      </div>
    );
  }

  if (analysisError) {
    return (
      <Alert variant="error">
        {analysisError instanceof Error ? analysisError.message : "Could not load analysis"}
      </Alert>
    );
  }

  if (!analysis) {
    return <Alert variant="info">Analysis not found.</Alert>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Analysis results</h1>
        <p className="mt-1 text-sm text-muted">
          {statement?.filename && (
            <>
              <span className="font-medium text-foreground">{statement.filename}</span>
              {" · "}
            </>
          )}
          Rules-based scan · {formatDate(analysis.created_at)}
          {!analysis.ai_enabled && " · AI enrichment off"}
        </p>
      </div>

      <AnalysisSummaryCards
        monthlyRecurringTotal={analysis.monthly_recurring_total}
        estimatedSavings={analysis.estimated_savings}
        avoidableFeesTotal={analysis.avoidable_fees_total}
        potentialSubscriptionSavings={analysis.potential_subscription_savings}
        currency={currency}
      />

      {analysis.spending_comparison && (
        <SpendingComparisonCard
          comparison={analysis.spending_comparison}
          estimatedSavings={analysis.potential_subscription_savings}
          currency={currency}
        />
      )}

      <SubscriptionList subscriptions={analysis.detected_subscriptions} subscriptionsCount={analysis.subscriptions_count} currency={currency} />

      <RecommendationList recommendations={analysis.recommendations} currency={currency} />

      {exportError && <Alert variant="error">{exportError}</Alert>}

    {/* Download analysis button and back to dashboard */}
    <div className="flex flex-wrap gap-2 justify-end ">
        <Button 
          type="button"
          variant="secondary" 
          loading={exporting}
          onClick={handleExport} 
          disabled={exporting}
          >
          Download analysis
        </Button>
        <Link href="/dashboard" className={buttonClass("secondary")}>
          Back to dashboard
        </Link>
      </div>
      
    </div>
  );
}
