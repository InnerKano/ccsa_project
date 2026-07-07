import Link from "next/link";

import { Button, Card, CardContent, Spinner } from "@/components/ui";
import type { AnalysisSummary } from "@/lib/api/analysis";
import type { StatementSummary } from "@/lib/api/statements";
import { formatCurrency, formatDate } from "@/lib/format";

type StatementCardProps = {
  statement: StatementSummary;
  latestAnalysis: AnalysisSummary | undefined;
  analyzing: boolean;
  archiving: boolean;
  onRunAnalysis: (statementId: string) => void;
  onArchive: (statementId: string) => void;
};

/** Outline trash glyph. Inline SVG avoids an icon dependency (DESIGN.md §8). */
function TrashIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path d="M3 6h18" />
      <path d="M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
      <path d="M10 11v6M14 11v6" />
    </svg>
  );
}

export function StatementCard({
  statement,
  latestAnalysis,
  analyzing,
  archiving,
  onRunAnalysis,
  onArchive,
}: StatementCardProps) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 space-y-1">
          <p className="truncate font-medium text-foreground">{statement.filename}</p>
          <p className="text-sm text-muted">
            {formatDate(statement.uploaded_at)} · {statement.transaction_count} transaction
            {statement.transaction_count === 1 ? "" : "s"} · {statement.currency}
          </p>
          {latestAnalysis && (
            <p className="text-sm text-foreground">
              Latest analysis:{" "}
              <span className="font-medium text-brand-700">
                {formatCurrency(latestAnalysis.estimated_savings, statement.currency)}
              </span>{" "}
              potential savings / mo
            </p>
          )}
        </div>

        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {latestAnalysis && (
            <Link
              href={`/analysis/${latestAnalysis.id}`}
              className="inline-flex h-9 items-center rounded-lg border border-border bg-surface px-3 text-sm font-medium text-foreground transition-colors hover:bg-surface-muted"
            >
              View results
            </Link>
          )}
          <Button
            type="button"
            variant={latestAnalysis ? "secondary" : "primary"}
            size="sm"
            loading={analyzing}
            onClick={() => onRunAnalysis(statement.id)}
          >
            {latestAnalysis ? "Re-run analysis" : "Run analysis"}
          </Button>
          {/* Low-emphasis destructive action, kept off the primary path so it does
              not clutter the card (DESIGN.md §2.1 restraint). Archive is reversible,
              so an Undo affordance (StatementList) stands in for a confirm dialog. */}
          <button
            type="button"
            onClick={() => onArchive(statement.id)}
            disabled={archiving}
            aria-label={`Archive ${statement.filename}`}
            title="Archive"
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-muted transition-colors hover:bg-danger-bg hover:text-danger focus-visible:text-danger disabled:cursor-not-allowed disabled:opacity-60"
          >
            {archiving ? <Spinner size={16} /> : <TrashIcon />}
          </button>
        </div>
      </CardContent>
    </Card>
  );
}
