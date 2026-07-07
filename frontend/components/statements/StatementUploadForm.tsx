"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { Alert, Button, Field, inputClassName } from "@/components/ui";
import { ApiError } from "@/lib/api/client";
import { cn } from "@/lib/cn";
import {
  isAllowedStatementFile,
  uploadStatement,
  type DecimalStyle,
} from "@/lib/api/statements";

type UploadPhase = "idle" | "uploading" | "processing";

const DECIMAL_STYLES: { value: DecimalStyle; label: string }[] = [
  { value: "auto", label: "Auto-detect" },
  { value: "us", label: "US (1,234.56)" },
  { value: "eu", label: "EU / LatAm (1.234,56)" },
];

const CURRENCIES = ["USD", "EUR", "COP", "MXN", "GBP"] as const;

/**
 * Statement upload form — POST /api/statements (CSV/TSV/TXT or PDF).
 * Primary path: file + currency. Advanced column/locale overrides live in
 * a <details> block (progressive disclosure, DESIGN.md §1).
 */
export function StatementUploadForm() {
  const router = useRouter();

  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [currency, setCurrency] = useState("USD");
  const [decimalStyle, setDecimalStyle] = useState<DecimalStyle>("auto");
  const [dayfirst, setDayfirst] = useState<"" | "true" | "false">("");
  const [dateColumn, setDateColumn] = useState("");
  const [descriptionColumn, setDescriptionColumn] = useState("");
  const [amountColumn, setAmountColumn] = useState("");
  const [debitColumn, setDebitColumn] = useState("");
  const [creditColumn, setCreditColumn] = useState("");
  const [dateFormat, setDateFormat] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [phase, setPhase] = useState<UploadPhase>("idle");
  const [progress, setProgress] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [interrupted, setInterrupted] = useState(false);

  const busy = phase !== "idle";

  // Elapsed-seconds ticker so a slow upload/parse reads as active work, not a
  // frozen screen (mobile networks + server-side parsing can take ~20s+).
  useEffect(() => {
    if (!busy) return;
    const started = Date.now();
    setElapsed(0);
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(id);
  }, [busy]);

  function handleFileChange(selected: File | null) {
    setFileError(null);
    if (!selected) {
      setFile(null);
      return;
    }
    if (!isAllowedStatementFile(selected)) {
      setFile(null);
      setFileError("File must be a CSV/TSV/TXT export or a bank statement PDF");
      return;
    }
    setFile(selected);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setError(null);
    setInterrupted(false);

    if (!file) {
      setFileError("Choose a statement file to upload");
      return;
    }

    setPhase("uploading");
    setProgress(0);
    const startedAt = Date.now();
    try {
      const result = await uploadStatement(
        file,
        {
          currency: currency.toUpperCase(),
          decimal_style: decimalStyle,
          ...(dayfirst !== "" ? { dayfirst: dayfirst === "true" } : {}),
          ...(dateColumn.trim() ? { date_column: dateColumn.trim() } : {}),
          ...(descriptionColumn.trim() ? { description_column: descriptionColumn.trim() } : {}),
          ...(amountColumn.trim() ? { amount_column: amountColumn.trim() } : {}),
          ...(debitColumn.trim() ? { debit_column: debitColumn.trim() } : {}),
          ...(creditColumn.trim() ? { credit_column: creditColumn.trim() } : {}),
          ...(dateFormat.trim() ? { date_format: dateFormat.trim() } : {}),
        },
        {
          onProgress: (percent) => setProgress(percent),
          onProcessing: () => setPhase("processing"),
        },
      );

      console.info(`[CCSA] statement upload + parse took ${Math.round((Date.now() - startedAt) / 1000)}s`);
      router.push(
        `/dashboard?uploaded=${encodeURIComponent(result.id)}&count=${result.transaction_count}`,
      );
    } catch (err) {
      // Status 0 = transport dropped after the file was sent — the server may
      // have finished anyway, so steer the user to check instead of re-uploading.
      if (err instanceof ApiError && err.status === 0) {
        setInterrupted(true);
      } else {
        setError(err instanceof Error ? err.message : "Upload failed");
      }
      setPhase("idle");
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-6">
      <div className="space-y-1.5">
        <label htmlFor="statement-file" className="block text-sm font-medium text-foreground">
          Statement file
        </label>
        <input
          id="statement-file"
          type="file"
          accept=".csv,.tsv,.txt,.pdf,text/csv,text/tab-separated-values,text/plain,application/pdf"
          className={cn(
            inputClassName,
            "file:mr-3 file:rounded-md file:border-0 file:bg-brand-50 file:px-3 file:py-1 file:text-sm file:font-medium file:text-brand-800",
            fileError && "border-danger focus:border-danger",
          )}
          aria-invalid={fileError ? true : undefined}
          disabled={busy}
          onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
        />
        {fileError ? (
          <p className="text-xs text-danger">{fileError}</p>
        ) : (
          <p className="text-xs text-muted">
            CSV, TSV, TXT export, or PDF bank/card statement. Your raw file is never stored —
            only normalized transactions are saved.
          </p>
        )}
        {file && !fileError && (
          <p className="text-xs text-foreground">
            Selected: <span className="font-medium">{file.name}</span>
          </p>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label htmlFor="currency" className="block text-sm font-medium text-foreground">
            Currency
          </label>
          <select
            id="currency"
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            className={inputClassName}
            disabled={busy}
          >
            {CURRENCIES.map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </select>
          <p className="text-xs text-muted">Single currency per statement (no conversion).</p>
        </div>

        <div className="space-y-1.5">
          <label htmlFor="decimal-style" className="block text-sm font-medium text-foreground">
            Number format
          </label>
          <select
            id="decimal-style"
            value={decimalStyle}
            onChange={(e) => setDecimalStyle(e.target.value as DecimalStyle)}
            className={inputClassName}
            disabled={busy}
          >
            {DECIMAL_STYLES.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <details className="rounded-lg border border-border bg-surface-muted px-4 py-3">
        <summary className="cursor-pointer text-sm font-medium text-foreground">
          Advanced column mapping
        </summary>
        <p className="mt-2 text-xs text-muted">
          Leave blank to auto-detect date, description, and amount columns (English and
          Spanish headers). Use when your export uses non-standard names or separate
          debit/credit columns.
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <Field
            label="Date column"
            id="date-column"
            value={dateColumn}
            onChange={(e) => setDateColumn(e.target.value)}
            placeholder="e.g. Transaction Date"
          />
          <Field
            label="Description column"
            id="description-column"
            value={descriptionColumn}
            onChange={(e) => setDescriptionColumn(e.target.value)}
            placeholder="e.g. Description"
          />
          <Field
            label="Amount column"
            id="amount-column"
            value={amountColumn}
            onChange={(e) => setAmountColumn(e.target.value)}
            placeholder="e.g. Amount"
          />
          <Field
            label="Debit column"
            id="debit-column"
            value={debitColumn}
            onChange={(e) => setDebitColumn(e.target.value)}
            placeholder="Optional"
          />
          <Field
            label="Credit column"
            id="credit-column"
            value={creditColumn}
            onChange={(e) => setCreditColumn(e.target.value)}
            placeholder="Optional"
          />
          <Field
            label="Date format"
            id="date-format"
            value={dateFormat}
            onChange={(e) => setDateFormat(e.target.value)}
            placeholder="e.g. %d/%m/%Y"
          />
          <div className="space-y-1.5">
            <label htmlFor="dayfirst" className="block text-sm font-medium text-foreground">
              Date order
            </label>
            <select
              id="dayfirst"
              value={dayfirst}
              onChange={(e) => setDayfirst(e.target.value as "" | "true" | "false")}
              className={inputClassName}
            >
              <option value="">Auto-detect</option>
              <option value="true">Day first (DD/MM)</option>
              <option value="false">Month first (MM/DD)</option>
            </select>
          </div>
        </div>
      </details>

      {error && <Alert variant="error">{error}</Alert>}

      {interrupted && (
        <Alert variant="info">
          The connection dropped while uploading, but your statement may have finished processing.
          Check your{" "}
          <Link href="/dashboard" className="font-medium underline">
            dashboard
          </Link>{" "}
          before uploading again to avoid a duplicate.
        </Alert>
      )}

      {busy ? (
        <div className="space-y-2" role="status" aria-live="polite">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-foreground">
              {phase === "uploading" ? "Uploading your statement…" : "Analyzing your statement…"}
            </span>
            <span className="tabular-nums text-muted">
              {phase === "uploading" ? `${progress}%` : `${elapsed}s`}
            </span>
          </div>
          <div
            className="h-2 w-full overflow-hidden rounded-full bg-surface-muted"
            role="progressbar"
            aria-label={phase === "uploading" ? "Upload progress" : "Analysis in progress"}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={phase === "uploading" ? progress : undefined}
          >
            <div
              className={cn(
                "h-full rounded-full bg-brand-600",
                phase === "uploading"
                  ? "transition-[width] duration-300 ease-out"
                  : "w-full animate-pulse",
              )}
              style={phase === "uploading" ? { width: `${progress}%` } : undefined}
            />
          </div>
          <p className="text-xs text-muted">
            {phase === "uploading"
              ? "Sending your file securely. Larger files or slower connections take longer."
              : "Parsing transactions on the server. This can take up to a minute on mobile networks — please keep this page open."}
          </p>
        </div>
      ) : (
        <Button type="submit" className="w-full sm:w-auto" disabled={!file}>
          Upload statement
        </Button>
      )}
    </form>
  );
}
