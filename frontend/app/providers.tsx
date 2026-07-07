"use client";

/**
 * App-wide client providers: SWR (data fetching/cache) + auth session.
 *
 * The default SWR fetcher is the shared API client, so any hook can do
 * `useSWR("/api/statements")` and get typed, authenticated data with caching
 * and revalidation. Kept in one place so pages/components stay declarative.
 */
import { SWRConfig } from "swr";
import type { ReactNode } from "react";

import { apiFetch } from "@/lib/api/client";
import { AuthProvider } from "@/lib/auth/context";
import { ThemeProvider } from "@/lib/theme/context";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <SWRConfig
      value={{
        fetcher: (path: string) => apiFetch(path),
        revalidateOnFocus: false,
        shouldRetryOnError: false,
      }}
    >
      <ThemeProvider>
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </SWRConfig>
  );
}
