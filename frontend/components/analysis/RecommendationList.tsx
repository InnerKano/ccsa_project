import { Card, CardContent, CardTitle } from "@/components/ui";
import type { Recommendation } from "@/lib/api/analysis";
import { formatCurrency } from "@/lib/format";

type RecommendationListProps = {
  recommendations: Recommendation[];
  currency?: string;
};

export function RecommendationList({
  recommendations,
  currency = "USD",
}: RecommendationListProps) {
  return (
    <Card>
      <CardContent>
        <CardTitle>Recommendations</CardTitle>
        <p className="mt-1 text-sm text-muted">
          Actionable ways to cut avoidable fees and recurring spending.
        </p>

        {recommendations.length === 0 ? (
          <p className="mt-4 text-sm text-muted">
            No savings opportunities were flagged. Essential recurring charges may still appear in
            the list above.
          </p>
        ) : (
          <ul className="mt-4 space-y-4" role="list">
            {recommendations.map((rec) => (
              <li
                key={`${rec.kind}-${rec.title}-${rec.estimated_saving}`}
                className="rounded-lg border border-border bg-surface-muted px-4 py-3"
              >
                <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                  <p className="font-medium text-foreground">{rec.title}</p>
                  <RecommendationBadge recommendation={rec} currency={currency} />
                </div>
                <p className="mt-2 text-sm text-muted">{rec.detail}</p>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function RecommendationBadge({
  recommendation,
  currency,
}: {
  recommendation: Recommendation;
  currency: string;
}) {
  if (recommendation.kind === "review_subscription") {
    return (
      <span className="shrink-0 rounded-full bg-surface px-2.5 py-0.5 text-xs font-medium text-muted">
        Worth reviewing
      </span>
    );
  }

  const suffix = recommendation.kind === "cancel_subscription" ? "/mo" : "";
  return (
    <p className="shrink-0 text-sm font-semibold text-brand-700">
      Save {formatCurrency(recommendation.estimated_saving, currency)}
      {suffix}
    </p>
  );
}
