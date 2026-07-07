"use client";

import Link from "next/link";
import { useState } from "react";
import useSWR, { mutate as globalMutate } from "swr";

import { ArchivedStatementCard } from "@/components/dashboard/ArchivedStatementCard";
import { Alert, buttonClass, Card, CardContent, CardTitle, Spinner } from "@/components/ui";
import {
  deleteStatementPermanent,
  listArchivedStatements,
  restoreStatement,
} from "@/lib/api/statements";

export function ArchivedList() {
  const [restoringId, setRestoringId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const {
    data: archived,
    error,
    isLoading,
    mutate: mutateArchived,
  } = useSWR("archived-statements", listArchivedStatements);

  async function handleRestore(statementId: string) {
    setActionError(null);
    setRestoringId(statementId);
    try {
      await restoreStatement(statementId);
      await mutateArchived();
      // Bring it back on the dashboard views too.
      await globalMutate("statements");
      await globalMutate("analyses");
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not restore statement");
    } finally {
      setRestoringId(null);
    }
  }

  async function handleDelete(statementId: string) {
    setActionError(null);
    setDeletingId(statementId);
    try {
      await deleteStatementPermanent(statementId);
      await mutateArchived();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not delete statement");
    } finally {
      setDeletingId(null);
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-12" role="status" aria-label="Loading archived statements">
        <Spinner size={32} />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="error">
        {error instanceof Error ? error.message : "Could not load archived statements"}
      </Alert>
    );
  }

  if (!archived || archived.length === 0) {
    return (
      <Card>
        <CardContent>
          <CardTitle>No archived statements</CardTitle>
          <p className="mt-2 text-sm text-muted">
            Statements you archive from the dashboard appear here. They stay hidden but
            recoverable until you delete them permanently.
          </p>
          <Link href="/dashboard" className={`${buttonClass("secondary")} mt-4 inline-flex`}>
            Back to dashboard
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {actionError && <Alert variant="error">{actionError}</Alert>}
      {archived.map((statement) => (
        <ArchivedStatementCard
          key={statement.id}
          statement={statement}
          restoring={restoringId === statement.id}
          deleting={deletingId === statement.id}
          onRestore={handleRestore}
          onDelete={handleDelete}
        />
      ))}
    </div>
  );
}
