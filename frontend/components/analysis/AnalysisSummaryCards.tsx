import { Card, CardContent } from "@/components/ui";
import { formatCurrency } from "@/lib/format";

type AnalysisSummaryCardsProps = {
  monthlyRecurringTotal: string;
  estimatedSavings: string;
  avoidableFeesTotal?: string;
  potentialSubscriptionSavings?: string;
  currency?: string;
};

export function AnalysisSummaryCards({
  monthlyRecurringTotal,
  estimatedSavings,
  avoidableFeesTotal = "0",
  potentialSubscriptionSavings = "0",
  currency = "USD",
}: AnalysisSummaryCardsProps) {
  const fees = Number(avoidableFeesTotal);
  const subs = Number(potentialSubscriptionSavings);
  const hasFees = Number.isFinite(fees) && fees > 0;
  const hasSubs = Number.isFinite(subs) && subs > 0;

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
          {hasFees || hasSubs ? (
            <dl className="mt-2 space-y-1 text-xs text-muted">
              {hasFees && (
                <div className="flex items-center justify-between gap-2">
                  <dt>Avoidable fees (already paid)</dt>
                  <dd className="font-medium text-foreground">
                    {formatCurrency(avoidableFeesTotal, currency)}
                  </dd>
                </div>
              )}
              {hasSubs && (
                <div className="flex items-center justify-between gap-2">
                  <dt>Discretionary subscriptions</dt>
                  <dd className="font-medium text-foreground">
                    {formatCurrency(potentialSubscriptionSavings, currency)}
                  </dd>
                </div>
              )}
            </dl>
          ) : (
            <p className="mt-1 text-xs text-muted">
              Discretionary subscriptions and avoidable fees only — essentials are listed below
              but not flagged for cancellation.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
