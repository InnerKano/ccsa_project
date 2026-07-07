"use client";

import { useMemo } from "react";

import { DonutChart } from "@/components/ui/DonutChart";
import type { CategorySpendSlice } from "@/lib/api/analysis";
import { formatCategoryLabel } from "@/lib/analysis/chartColors";
import { formatCurrency } from "@/lib/format";

type SpendingDonutPanelProps = {
  title: string;
  subtitle: string;
  slices: CategorySpendSlice[];
  categoryColors: Map<string, string>;
  currency?: string;
};

function sliceTotal(slices: CategorySpendSlice[]): number {
  return slices.reduce((sum, slice) => sum + Number(slice.amount), 0);
}

function formatPercentage(value: string): string {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return value;
  return `${parsed.toFixed(1)}%`;
}

export function SpendingDonutPanel({
  title,
  subtitle,
  slices,
  categoryColors,
  currency = "USD",
}: SpendingDonutPanelProps) {
  const total = useMemo(() => sliceTotal(slices), [slices]);

  const segments = useMemo(
    () =>
      slices.map((slice) => ({
        id: slice.category,
        value: Number(slice.amount),
        color: categoryColors.get(slice.category) ?? "var(--color-chart-8)",
        label: formatCategoryLabel(slice.category),
      })),
    [slices, categoryColors],
  );

  return (
    <div className="flex min-w-0 flex-1 flex-col">
      <div>
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <p className="mt-0.5 text-sm text-muted">{subtitle}</p>
      </div>

      <div className="mt-5 flex flex-col items-center gap-6 sm:flex-row sm:items-start">
        <DonutChart segments={segments} total={total} currency={currency} />

        <ul className="w-full min-w-0 flex-1 space-y-3" role="list">
          {slices.map((slice) => (
            <li
              key={slice.category}
              className="flex items-center justify-between gap-3 text-sm"
            >
              <div className="flex min-w-0 items-center gap-2">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{
                    backgroundColor:
                      categoryColors.get(slice.category) ?? "var(--color-chart-8)",
                  }}
                  aria-hidden
                />
                <span className="truncate capitalize text-foreground">
                  {formatCategoryLabel(slice.category)}
                </span>
              </div>
              <div className="shrink-0 text-right tabular-nums">
                <span className="font-medium text-foreground">
                  {formatCurrency(slice.amount, currency)}
                </span>
                <span className="ml-2 text-muted">
                  {formatPercentage(slice.percentage)}
                </span>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
