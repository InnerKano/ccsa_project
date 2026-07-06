/**
 * Display formatting for values that arrive from the API.
 *
 * Money is serialized by the backend as decimal strings (docs/API.md) to keep
 * exact precision on the wire. We only convert to Number at the very edge, for
 * `Intl.NumberFormat` display — amounts are 2-decimal money well within the
 * safe-integer range, so no precision is lost in the rendered output.
 */
export function formatCurrency(value: string | number, currency = "USD"): string {
  const amount = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(amount)) return String(value);
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    // Unknown currency code → fall back to the numeric value with the code.
    return `${amount.toFixed(2)} ${currency}`;
  }
}

export function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
}
