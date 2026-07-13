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

export type RecommendationKind =
  | "cancel_subscription"
  | "review_subscription"
  | "avoid_fee";

export type Recommendation = {
  title: string;
  detail: string;
  estimated_saving: string;
  kind: RecommendationKind;
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
  // Savings split (D21): estimated_savings === avoidable_fees_total + potential_subscription_savings.
  avoidable_fees_total: string;
  potential_subscription_savings: string;
  subscriptions_count: number;
  detected_subscriptions: DetectedSubscription[];
  recommendations: Recommendation[];
  spending_comparison?: SpendingComparison;
};

export function runAnalysis(statementId: string): Promise<AnalysisDetail> {
  return apiFetch<AnalysisDetail>(`/api/analysis/${statementId}`, { method: "POST" });
}

export function listAnalyses(): Promise<AnalysisSummary[]> {
  // Trailing slash matches the FastAPI collection route (avoids a 307 redirect).
  return apiFetch<AnalysisSummary[]>("/api/analysis/");
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
