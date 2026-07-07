import { useState } from "react";

import { Button, Card, CardContent } from "@/components/ui";
import type { StatementSummary } from "@/lib/api/statements";
import { formatDate } from "@/lib/format";

type ArchivedStatementCardProps = {
  statement: StatementSummary;
  restoring: boolean;
  deleting: boolean;
  onRestore: (statementId: string) => void;
  onDelete: (statementId: string) => void;
};

export function ArchivedStatementCard({
  statement,
  restoring,
  deleting,
  onRestore,
  onDelete,
}: ArchivedStatementCardProps) {
  // Two-step inline confirm: permanent deletion is irreversible, so it requires an
  // explicit confirmation (DESIGN.md §6) — done inline to avoid a modal primitive.
  const [confirming, setConfirming] = useState(false);
  const busy = restoring || deleting;

  return (
    <Card>
      <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 space-y-1">
          <p className="truncate font-medium text-foreground">{statement.filename}</p>
          <p className="text-sm text-muted">
            {statement.transaction_count} transaction
            {statement.transaction_count === 1 ? "" : "s"} · {statement.currency}
            {statement.deleted_at && <> · Archived {formatDate(statement.deleted_at)}</>}
          </p>
        </div>

        {confirming ? (
          <div className="flex shrink-0 flex-col gap-2 sm:items-end">
            <p className="text-sm text-danger">Delete permanently? This can’t be undone.</p>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setConfirming(false)}
                disabled={busy}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="danger"
                size="sm"
                loading={deleting}
                onClick={() => onDelete(statement.id)}
              >
                Delete permanently
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              loading={restoring}
              onClick={() => onRestore(statement.id)}
            >
              Restore
            </Button>
            <button
              type="button"
              onClick={() => setConfirming(true)}
              disabled={busy}
              className="inline-flex h-9 items-center rounded-lg px-3 text-sm font-medium text-muted transition-colors hover:bg-danger-bg hover:text-danger focus-visible:text-danger disabled:cursor-not-allowed disabled:opacity-60"
            >
              Delete permanently
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
