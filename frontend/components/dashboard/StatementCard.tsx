import Link from "next/link";

import { Button, Card, CardContent } from "@/components/ui";
import type { AnalysisSummary } from "@/lib/api/analysis";
import type { StatementSummary } from "@/lib/api/statements";
import { formatCurrency, formatDate } from "@/lib/format";

type StatementCardProps = {
  statement: StatementSummary;
  latestAnalysis: AnalysisSummary | undefined;
  analyzing: boolean;
  onRunAnalysis: (statementId: string) => void;
};

export function StatementCard({
  statement,
  latestAnalysis,
  analyzing,
  onRunAnalysis,
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

        <div className="flex shrink-0 flex-wrap gap-2">
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
        </div>
      </CardContent>
    </Card>
  );
}
