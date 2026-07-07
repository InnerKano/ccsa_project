"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import useSWR from "swr";

import { StatementCard } from "@/components/dashboard/StatementCard";
import { Alert, buttonClass, Card, CardContent, CardTitle, Spinner } from "@/components/ui";
import { latestAnalysisByStatement, listAnalyses, runAnalysis } from "@/lib/api/analysis";
import { archiveStatement, listStatements, restoreStatement } from "@/lib/api/statements";

export function StatementList() {
  const router = useRouter();
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);
  const [archivingId, setArchivingId] = useState<string | null>(null);
  const [archived, setArchived] = useState<{ id: string; filename: string } | null>(null);
  const [restoring, setRestoring] = useState(false);
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

  async function handleArchive(statementId: string) {
    setActionError(null);
    const filename =
      statements?.find((s) => s.id === statementId)?.filename ?? "Statement";
    setArchivingId(statementId);
    try {
      await archiveStatement(statementId);
      await mutateStatements();
      await mutateAnalyses();
      // Reversible action → offer Undo instead of a blocking confirm dialog.
      setArchived({ id: statementId, filename });
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not archive statement");
    } finally {
      setArchivingId(null);
    }
  }

  async function handleUndoArchive() {
    if (!archived) return;
    setActionError(null);
    setRestoring(true);
    try {
      await restoreStatement(archived.id);
      await mutateStatements();
      await mutateAnalyses();
      setArchived(null);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not restore statement");
    } finally {
      setRestoring(false);
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

  const archivedNotice = archived && (
    <Alert variant="success">
      <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <span>
          <span className="font-medium">{archived.filename}</span> archived.
        </span>
        <button
          type="button"
          className="font-medium underline disabled:opacity-60"
          onClick={handleUndoArchive}
          disabled={restoring}
        >
          {restoring ? "Restoring…" : "Undo"}
        </button>
        <button
          type="button"
          className="text-muted underline"
          onClick={() => setArchived(null)}
        >
          Dismiss
        </button>
      </span>
    </Alert>
  );

  if (!statements || statements.length === 0) {
    return (
      <div className="space-y-4">
        {actionError && <Alert variant="error">{actionError}</Alert>}
        {archivedNotice}
        <Card>
          <CardContent>
            <CardTitle>No statements yet</CardTitle>
            <p className="mt-2 text-sm text-muted">
              Upload a statement export (CSV/TSV/TXT) or bank PDF to detect subscriptions and
              estimate savings.
            </p>
            <Link href="/upload" className={`${buttonClass("primary")} mt-4 inline-flex`}>
              Upload statement
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {actionError && <Alert variant="error">{actionError}</Alert>}
      {archivedNotice}
      {statements.map((statement) => (
        <StatementCard
          key={statement.id}
          statement={statement}
          latestAnalysis={analysisMap.get(statement.id)}
          analyzing={analyzingId === statement.id}
          archiving={archivingId === statement.id}
          onRunAnalysis={handleRunAnalysis}
          onArchive={handleArchive}
        />
      ))}
    </div>
  );
}
