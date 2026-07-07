import type { CategorySpendSlice } from "@/lib/api/analysis";

/** CSS variable references — resolved from tokens in `app/globals.css`. */
const CHART_COLOR_VARS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
  "var(--color-chart-6)",
  "var(--color-chart-7)",
  "var(--color-chart-8)",
] as const;

/** Stable color per category — same map for before and after panels. */
export function buildCategoryColorMap(categories: string[]): Map<string, string> {
  const map = new Map<string, string>();
  categories.forEach((category, index) => {
    map.set(category, CHART_COLOR_VARS[index % CHART_COLOR_VARS.length]);
  });
  return map;
}

/** Primary order from before slices (descending spend); append any after-only keys. */
export function orderedCategoriesForComparison(
  before: CategorySpendSlice[],
  after: CategorySpendSlice[],
): string[] {
  const order = before.map((slice) => slice.category);
  const seen = new Set(order);
  for (const slice of after) {
    if (!seen.has(slice.category)) {
      order.push(slice.category);
      seen.add(slice.category);
    }
  }
  return order;
}

export function formatCategoryLabel(category: string): string {
  return category.replace(/_/g, " ");
}
