"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import useSWR from "swr";

import { StatementCard } from "@/components/dashboard/StatementCard";
import { Alert, buttonClass, Card, CardContent, CardTitle, Spinner } from "@/components/ui";
import { latestAnalysisByStatement, listAnalyses, runAnalysis } from "@/lib/api/analysis";
import { listStatements } from "@/lib/api/statements";

export function StatementList() {
  const router = useRouter();
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const {
    data: statements,
    error: statementsError,
    isLoading: statementsLoading,
    mutate: mutateStatements,
  } = useSWR("statements", listStatements);

  const {
    data: analyses,
    error: analysesError,
    isLoading: analysesLoading,
    mutate: mutateAnalyses,
  } = useSWR("analyses", listAnalyses);

  const analysisMap = analyses ? latestAnalysisByStatement(analyses) : new Map();

  async function handleRunAnalysis(statementId: string) {
    setActionError(null);
    setAnalyzingId(statementId);
    try {
      const result = await runAnalysis(statementId);
      await mutateAnalyses();
      await mutateStatements();
      router.push(`/analysis/${result.id}`);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setAnalyzingId(null);
    }
  }

  if (statementsLoading || analysesLoading) {
    return (
      <div className="flex justify-center py-12" role="status" aria-label="Loading statements">
        <Spinner size={32} />
      </div>
    );
  }

  if (statementsError || analysesError) {
    return (
      <Alert variant="error">
        {statementsError instanceof Error
          ? statementsError.message
          : analysesError instanceof Error
            ? analysesError.message
            : "Could not load dashboard data"}
      </Alert>
    );
  }

  if (!statements || statements.length === 0) {
    return (
      <Card>
        <CardContent>
          <CardTitle>No statements yet</CardTitle>
          <p className="mt-2 text-sm text-muted">
            Upload a CSV export from your bank to detect subscriptions and estimate savings.
          </p>
          <Link href="/upload" className={`${buttonClass("primary")} mt-4 inline-flex`}>
            Upload statement
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {actionError && <Alert variant="error">{actionError}</Alert>}
      {statements.map((statement) => (
        <StatementCard
          key={statement.id}
          statement={statement}
          latestAnalysis={analysisMap.get(statement.id)}
          analyzing={analyzingId === statement.id}
          onRunAnalysis={handleRunAnalysis}
        />
      ))}
    </div>
  );
}
