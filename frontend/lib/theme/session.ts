import type { ThemePreference } from "./resolve";

/**
 * Theme preference persistence.
 *
 * Single source of truth for where the user's theme choice lives. Stored in
 * `localStorage` (MVP): simple, survives reloads, no backend needed.
 */
export const THEME_STORAGE_KEY = "ccsa_theme";

export function getThemePreference(): ThemePreference {
  if (typeof window === "undefined") return "system";
  const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === "light" || stored === "dark" || stored === "system") return stored;
  return "system";
}

export function saveThemePreference(theme: ThemePreference): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(THEME_STORAGE_KEY, theme);
}
