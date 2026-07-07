import { Card, CardContent, CardTitle } from "@/components/ui";
import type { DetectedSubscription } from "@/lib/api/analysis";
import { cn } from "@/lib/cn";
import { formatCurrency } from "@/lib/format";

function formatCategoryLabel(category: string | null): string {
  if (!category) return "Uncategorized";
  return category.replace(/_/g, " ");
}

function formatCadenceLabel(cadence: string): string {
  switch (cadence) {
    case "monthly":
      return "Monthly";
    case "suspected":
      return "Suspected (single statement)";
    default:
      return cadence.replace(/_/g, " ");
  }
}

type SubscriptionListProps = {
  subscriptions: DetectedSubscription[];
  currency?: string;
};

export function SubscriptionList({ subscriptions, currency = "USD" }: SubscriptionListProps) {
  return (
    <Card>
      <CardContent>
        <CardTitle>Detected subscriptions</CardTitle>
        <p className="mt-1 text-sm text-muted">
          Recurring charges with stable amounts across multiple months.
        </p>

        {subscriptions.length === 0 ? (
          <p className="mt-4 text-sm text-muted">
            No recurring subscriptions were detected in this statement.
          </p>
        ) : (
          <ul className="mt-4 divide-y divide-border" role="list">
            {subscriptions.map((sub) => (
              <li
                key={`${sub.merchant}-${sub.amount}-${sub.cadence}`}
                className="flex flex-col gap-2 py-4 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0">
                  <p className="font-medium text-foreground">{sub.merchant}</p>
                  <p className="text-sm text-muted">
                    {formatCadenceLabel(sub.cadence)}
                    {sub.category && (
                      <>
                        {" · "}
                        <span
                          className={cn(
                            "inline-flex rounded-md bg-surface-muted px-2 py-0.5 text-xs font-medium text-foreground",
                          )}
                        >
                          {formatCategoryLabel(sub.category)}
                        </span>
                      </>
                    )}
                  </p>
                </div>
                <p className="shrink-0 text-sm font-semibold text-foreground">
                  {formatCurrency(sub.amount, currency)}
                  <span className="font-normal text-muted"> / mo</span>
                </p>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
