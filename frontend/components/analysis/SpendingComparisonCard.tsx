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
  const annualSavings = savingsAmount * 12;

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
          />
        </div>

        {hasSavings && (
          <SavingsInsightCard
            monthlySavings={formatCurrency(estimatedSavings, currency)}
            annualSavings={formatCurrency(annualSavings, currency)}
          />
        )}
      </CardContent>
    </Card>
  );
}

type SavingsInsightCardProps = {
  monthlySavings: string;
  annualSavings: string;
};

function SavingsInsightCard({ monthlySavings, annualSavings }: SavingsInsightCardProps) {
  return (
    <div className="relative mt-8 overflow-hidden rounded-[var(--radius-card)] border border-border bg-background px-6 py-5">
      <div className="relative z-10 flex items-center gap-4">
        <span
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-700"
          aria-hidden
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M20 6 9 17l-5-5" />
          </svg>
        </span>
        <div className="min-w-0">
          <p className="text-base font-semibold text-foreground">
            Good news! After removing discretionary subscriptions, you save{" "}
            {monthlySavings} every month.
          </p>
          <p className="mt-1 text-sm text-muted">
            That&apos;s{" "}
            <span className="font-semibold text-brand-700">{annualSavings}</span> per
            year kept in your pocket.
          </p>
        </div>
      </div>

      <div
        className="pointer-events-none absolute inset-y-0 right-0 hidden w-1/3 max-w-[240px] [mask-image:linear-gradient(to_right,transparent,#000_30%,#000_70%,transparent)] [-webkit-mask-image:linear-gradient(to_right,transparent,#000_30%,#000_70%,transparent)] sm:block"
        aria-hidden
      >
        <svg
          className="h-full w-full text-brand-500"
          viewBox="0 0 240 64"
          fill="none"
          preserveAspectRatio="xMaxYMid meet"
        >
          <path
            d="M240 32 Q 205 10 170 30 T 100 28 T 0 34"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeDasharray="1.5 9"
          />
        </svg>
      </div>
    </div>
  );
}
