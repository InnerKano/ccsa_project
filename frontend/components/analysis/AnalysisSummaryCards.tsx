import { Card, CardContent } from "@/components/ui";
import { formatCurrency } from "@/lib/format";

type AnalysisSummaryCardsProps = {
  monthlyRecurringTotal: string;
  estimatedSavings: string;
  currency?: string;
};

export function AnalysisSummaryCards({
  monthlyRecurringTotal,
  estimatedSavings,
  currency = "USD",
}: AnalysisSummaryCardsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Card>
        <CardContent>
          <p className="text-sm text-muted">Monthly recurring total</p>
          <p className="mt-1 text-2xl font-semibold text-foreground">
            {formatCurrency(monthlyRecurringTotal, currency)}
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <p className="text-sm text-muted">Estimated savings</p>
          <p className="mt-1 text-2xl font-semibold text-brand-700">
            {formatCurrency(estimatedSavings, currency)}
          </p>
          <p className="mt-1 text-xs text-muted">
            Discretionary subscriptions only — essentials are listed below but not flagged for
            cancellation.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
