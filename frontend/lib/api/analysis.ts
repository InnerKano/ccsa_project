/**
 * Analysis API — run, list, and retrieve (docs/API.md).
 * Money fields arrive as decimal strings on the wire.
 */
import { apiFetch } from "@/lib/api/client";

export type AnalysisSummary = {
  id: string;
  statement_id: string;
  ai_enabled: boolean;
  monthly_recurring_total: string;
  estimated_savings: string;
  created_at: string;
};

export type DetectedSubscription = {
  merchant: string;
  amount: string;
  cadence: string;
  category: string | null;
};

export type Recommendation = {
  title: string;
  detail: string;
  estimated_saving: string;
};

export type CategorySpendSlice = {
  category: string;
  amount: string;
  percentage: string;
};

export type SpendingComparison = {
  before: CategorySpendSlice[];
  after: CategorySpendSlice[];
};

export type AnalysisDetail = AnalysisSummary & {
  detected_subscriptions: DetectedSubscription[];
  recommendations: Recommendation[];
  spending_comparison?: SpendingComparison;
};

export function runAnalysis(statementId: string): Promise<AnalysisDetail> {
  return apiFetch<AnalysisDetail>(`/api/analysis/${statementId}`, { method: "POST" });
}

export function listAnalyses(): Promise<AnalysisSummary[]> {
  return apiFetch<AnalysisSummary[]>("/api/analysis");
}

export function getAnalysis(analysisId: string): Promise<AnalysisDetail> {
  return apiFetch<AnalysisDetail>(`/api/analysis/${analysisId}`);
}

/** Latest analysis per statement (API returns analyses newest-first — D10). */
export function latestAnalysisByStatement(
  analyses: AnalysisSummary[],
): Map<string, AnalysisSummary> {
  const map = new Map<string, AnalysisSummary>();
  for (const analysis of analyses) {
    if (!map.has(analysis.statement_id)) {
      map.set(analysis.statement_id, analysis);
    }
  }
  return map;
}
