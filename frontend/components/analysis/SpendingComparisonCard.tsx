import { Card, CardContent } from "@/components/ui";
import { SpendingDonutPanel } from "@/components/analysis/SpendingDonutPanel";
import type { SpendingComparison } from "@/lib/api/analysis";
import {
  buildCategoryColorMap,
  orderedCategoriesForComparison,
} from "@/lib/analysis/chartColors";
import { formatCurrency } from "@/lib/format";

type SpendingComparisonCardProps = {
  comparison: SpendingComparison;
  estimatedSavings: string;
  currency?: string;
};

export function SpendingComparisonCard({
  comparison,
  estimatedSavings,
  currency = "USD",
}: SpendingComparisonCardProps) {
  if (comparison.before.length === 0) {
    return null;
  }

  const categoryOrder = orderedCategoriesForComparison(
    comparison.before,
    comparison.after,
  );
  const categoryColors = buildCategoryColorMap(categoryOrder);

  const savingsAmount = Number(estimatedSavings);
  const hasSavings = Number.isFinite(savingsAmount) && savingsAmount > 0;
  const savingsNote = hasSavings
    ? `✓ You'll save ${formatCurrency(estimatedSavings, currency)} / month`
    : "No discretionary savings flagged for this statement.";

  return (
    <Card>
      <CardContent>
        <div className="flex flex-col items-stretch gap-8 lg:flex-row lg:gap-10">
          <SpendingDonutPanel
            title="Before: Current recurring spend"
            subtitle="Based on detected recurring charges"
            slices={comparison.before}
            categoryColors={categoryColors}
            currency={currency}
          />

          <div
            className="flex shrink-0 items-center justify-center text-2xl text-muted lg:self-center"
            aria-hidden
          >
            <span className="hidden lg:inline">→</span>
            <span className="lg:hidden">↓</span>
          </div>

          <SpendingDonutPanel
            title="After: With recommended savings"
            subtitle="After removing discretionary subscriptions"
            slices={comparison.after}
            categoryColors={categoryColors}
            currency={currency}
            savingsNote={savingsNote}
            showSavingsNote
            highlightSavings={hasSavings}
          />
        </div>
      </CardContent>
    </Card>
  );
}
