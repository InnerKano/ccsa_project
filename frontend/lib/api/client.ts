/**
 * Low-level API client.
 *
 * Every request to the FastAPI backend goes through `apiFetch`, which:
 * - prefixes `NEXT_PUBLIC_API_URL`,
 * - attaches the Bearer token from the session (unless `auth: false`),
 * - serializes JSON bodies (or passes `FormData` through untouched for uploads),
 * - normalizes the backend's `{ "detail": "..." }` errors into `ApiError`.
 *
 * The backend returns resources directly (no envelope) and money as decimal
 * strings — see docs/API.md. This layer stays transport-only; feature modules
 * (api/auth.ts, api/statements.ts, ...) build typed calls on top of it.
 */
import { getToken } from "@/lib/auth/session";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  /** JSON-serializable body, or FormData for multipart uploads. */
  body?: unknown;
  /** Set false for endpoints that must not carry a token (register/login). */
  auth?: boolean;
  headers?: Record<string, string>;
};

async function extractDetail(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    // 422 validation errors arrive as an array of field errors.
    if (Array.isArray(data?.detail) && data.detail[0]?.msg) return data.detail[0].msg;
  } catch {
    /* fall through to a generic message */
  }
  return "Request failed";
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true, headers = {} } = options;

  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
  const finalHeaders: Record<string, string> = { ...headers };

  if (auth) {
    const token = getToken();
    if (token) finalHeaders.Authorization = `Bearer ${token}`;
  }

  let payload: BodyInit | undefined;
  if (body !== undefined) {
    if (isFormData) {
      payload = body as FormData; // let the browser set the multipart boundary
    } else {
      finalHeaders["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }
  }

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: finalHeaders,
    body: payload,
  });

  if (!res.ok) {
    throw new ApiError(res.status, await extractDetail(res));
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}
