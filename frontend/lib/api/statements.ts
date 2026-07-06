/**
 * Statements API — upload and list (docs/API.md).
 * Built on the shared apiFetch client; JWT is attached automatically.
 */
import { apiFetch } from "@/lib/api/client";

export type StatementSummary = {
  id: string;
  filename: string;
  currency: string;
  transaction_count: number;
  uploaded_at: string;
};

export type DecimalStyle = "auto" | "us" | "eu";

/** Optional multipart fields supported by POST /api/statements (API.md). */
export type UploadStatementOptions = {
  currency?: string;
  decimal_style?: DecimalStyle;
  dayfirst?: boolean;
  date_column?: string;
  description_column?: string;
  amount_column?: string;
  debit_column?: string;
  credit_column?: string;
  date_format?: string;
};

const ALLOWED_EXTENSIONS = [".csv", ".tsv", ".txt"];

export function isAllowedStatementFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return ALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext));
}

export function uploadStatement(
  file: File,
  options: UploadStatementOptions = {},
): Promise<StatementSummary> {
  const form = new FormData();
  form.append("file", file);

  const { currency = "USD", decimal_style = "auto", dayfirst, ...columns } = options;

  form.append("currency", currency);
  form.append("decimal_style", decimal_style);

  if (dayfirst !== undefined) {
    form.append("dayfirst", dayfirst ? "true" : "false");
  }

  const optionalFields: (keyof typeof columns)[] = [
    "date_column",
    "description_column",
    "amount_column",
    "debit_column",
    "credit_column",
    "date_format",
  ];

  for (const key of optionalFields) {
    const value = columns[key];
    if (value) form.append(key, value);
  }

  return apiFetch<StatementSummary>("/api/statements", {
    method: "POST",
    body: form,
  });
}

export function listStatements(): Promise<StatementSummary[]> {
  return apiFetch<StatementSummary[]>("/api/statements");
}

export type TransactionSummary = {
  id: string;
  date: string;
  description: string;
  amount: string;
  category: string | null;
};

export type StatementDetail = StatementSummary & {
  transactions: TransactionSummary[];
};

export function getStatement(statementId: string): Promise<StatementDetail> {
  return apiFetch<StatementDetail>(`/api/statements/${statementId}`);
}
