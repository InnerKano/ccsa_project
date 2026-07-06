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
          Actionable ideas to reduce discretionary recurring spending.
        </p>

        {recommendations.length === 0 ? (
          <p className="mt-4 text-sm text-muted">
            No discretionary savings opportunities were flagged. Essential recurring charges may
            still appear in the list above.
          </p>
        ) : (
          <ul className="mt-4 space-y-4" role="list">
            {recommendations.map((rec) => (
              <li
                key={`${rec.title}-${rec.estimated_saving}`}
                className="rounded-lg border border-border bg-surface-muted px-4 py-3"
              >
                <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                  <p className="font-medium text-foreground">{rec.title}</p>
                  <p className="shrink-0 text-sm font-semibold text-brand-700">
                    Save {formatCurrency(rec.estimated_saving, currency)}/mo
                  </p>
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
