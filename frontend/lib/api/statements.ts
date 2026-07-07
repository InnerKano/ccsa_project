/**
 * Statements API — upload and list (docs/API.md).
 * Built on the shared apiFetch client; JWT is attached automatically.
 */
import { API_URL, ApiError, apiFetch } from "@/lib/api/client";
import { getToken } from "@/lib/auth/session";

export type StatementSummary = {
  id: string;
  filename: string;
  currency: string;
  transaction_count: number;
  uploaded_at: string;
  /** Null for active statements; ISO timestamp when archived (D22). */
  deleted_at?: string | null;
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

const ALLOWED_EXTENSIONS = [".csv", ".tsv", ".txt", ".pdf"];

export function isAllowedStatementFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return ALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext));
}

/**
 * Progress hooks for the upload. `fetch` cannot report request-body upload
 * progress, so the upload uses XHR (below) to drive an honest two-phase UI:
 * a determinate % while the file is being sent, then an indeterminate
 * "processing" phase while the server parses it.
 */
export type UploadStatementHandlers = {
  /** Percentage (0–100) of the request body uploaded. */
  onProgress?: (percent: number) => void;
  /** File fully sent; the server is now parsing it (no client-side %). */
  onProcessing?: () => void;
};

/** Mirror of the JSON error shape from apiFetch (`{ detail }` / 422 array). */
function extractXhrDetail(xhr: XMLHttpRequest): string {
  try {
    const data = JSON.parse(xhr.responseText);
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail) && data.detail[0]?.msg) return data.detail[0].msg;
  } catch {
    /* fall through to a generic message */
  }
  return "Upload failed";
}

function buildStatementForm(file: File, options: UploadStatementOptions): FormData {
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

  return form;
}

export function uploadStatement(
  file: File,
  options: UploadStatementOptions = {},
  handlers: UploadStatementHandlers = {},
): Promise<StatementSummary> {
  const form = buildStatementForm(file, options);

  return new Promise<StatementSummary>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    // Trailing slash matches the FastAPI collection route exactly — avoids the
    // 307 redirect that mobile WebKit refuses to follow on a preflighted,
    // credentialed multipart POST.
    xhr.open("POST", `${API_URL}/api/statements/`);

    const token = getToken();
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);

    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable) return;
      const percent = Math.min(100, Math.round((event.loaded / event.total) * 100));
      handlers.onProgress?.(percent);
    };
    xhr.upload.onload = () => {
      handlers.onProgress?.(100);
      handlers.onProcessing?.();
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as StatementSummary);
        } catch {
          reject(new ApiError(xhr.status, "Malformed server response"));
        }
      } else {
        reject(new ApiError(xhr.status, extractXhrDetail(xhr)));
      }
    };
    // Status 0 = transport-level failure (network drop / timeout). The request
    // may still have completed server-side, so callers should not present this
    // as a hard "upload failed" that invites a duplicate re-upload.
    xhr.onerror = () => reject(new ApiError(0, "Connection interrupted"));
    xhr.ontimeout = () => reject(new ApiError(0, "Connection timed out"));

    xhr.send(form);
  });
}

export function listStatements(): Promise<StatementSummary[]> {
  return apiFetch<StatementSummary[]>("/api/statements/");
}

/** Soft-deleted statements for the "Archived" view (D22). */
export function listArchivedStatements(): Promise<StatementSummary[]> {
  return apiFetch<StatementSummary[]>("/api/statements/?archived=true");
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

/**
 * Soft-archive a statement (D22): hides it (and its analyses) from the dashboard
 * while it is retained server-side. Reversible with {@link restoreStatement}.
 */
export function archiveStatement(statementId: string): Promise<void> {
  return apiFetch<void>(`/api/statements/${statementId}`, { method: "DELETE" });
}

/** Undo an archive — powers the "Undo" affordance after archiving (D22). */
export function restoreStatement(statementId: string): Promise<StatementSummary> {
  return apiFetch<StatementSummary>(`/api/statements/${statementId}/restore`, {
    method: "POST",
  });
}

/**
 * Permanently erase a statement and all derived data (right to be forgotten, D22).
 * Not reversible — kept distinct from the everyday archive above.
 */
export function deleteStatementPermanent(statementId: string): Promise<void> {
  return apiFetch<void>(`/api/statements/${statementId}/permanent`, {
    method: "DELETE",
  });
}
