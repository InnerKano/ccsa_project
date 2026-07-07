/**
 * Auth API calls (register / login). Token persistence lives in
 * `lib/auth/session.ts`; session/UI state lives in `lib/auth/context.tsx`.
 * These functions are transport-only and reuse the shared `apiFetch` client.
 */
import { apiFetch } from "@/lib/api/client";

export type RegisterResult = {
  id: string;
  email: string;
  token: string;
};

export type LoginResult = {
  token: string;
};

export type MessageResult = {
  message: string;
};

export function register(email: string, password: string): Promise<RegisterResult> {
  return apiFetch<RegisterResult>("/api/auth/register", {
    method: "POST",
    body: { email, password },
    auth: false,
  });
}

export function login(email: string, password: string): Promise<LoginResult> {
  return apiFetch<LoginResult>("/api/auth/login", {
    method: "POST",
    body: { email, password },
    auth: false,
  });
}

/** Request a reset link. The backend responds identically whether or not the
 *  email exists (no account enumeration, D23), so the UI shows one message. */
export function forgotPassword(email: string): Promise<MessageResult> {
  return apiFetch<MessageResult>("/api/auth/forgot-password", {
    method: "POST",
    body: { email },
    auth: false,
  });
}

export function resetPassword(token: string, password: string): Promise<MessageResult> {
  return apiFetch<MessageResult>("/api/auth/reset-password", {
    method: "POST",
    body: { token, password },
    auth: false,
  });
}

// Re-exported for backwards compatibility with existing imports; the canonical
// home for these is `lib/auth/session.ts`.
export {
  TOKEN_STORAGE_KEY,
  getToken,
  saveToken,
  clearToken,
} from "@/lib/auth/session";
