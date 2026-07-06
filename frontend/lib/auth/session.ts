/**
 * JWT session persistence.
 *
 * Single source of truth for where the token lives. The token is stored in
 * `localStorage` (MVP): simple, survives reloads, and the API is stateless
 * (JWT). If XSS hardening becomes a requirement, this is the one place to swap
 * for httpOnly cookies — callers go through these helpers, not localStorage.
 */
export const TOKEN_STORAGE_KEY = "ccsa_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function saveToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}
