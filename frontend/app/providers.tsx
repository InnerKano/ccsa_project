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

import { apiFetch, ApiError } from "@/lib/api/client";
import { AuthProvider } from "@/lib/auth/context";
import { ThemeProvider } from "@/lib/theme/context";

// The backend runs on a free tier that sleeps when idle, so the first request
// after inactivity can fail or hang for ~15-30s (cold start). Retry transient
// network/5xx failures a few times so the UI self-heals instead of surfacing an
// error; never retry 4xx (auth/validation) — those are not transient.
const COLD_START_RETRY_COUNT = 5;
const COLD_START_RETRY_INTERVAL_MS = 3000;

export function Providers({ children }: { children: ReactNode }) {
  return (
    <SWRConfig
      value={{
        fetcher: (path: string) => apiFetch(path),
        revalidateOnFocus: false,
        errorRetryInterval: COLD_START_RETRY_INTERVAL_MS,
        onErrorRetry: (error, _key, _config, revalidate, { retryCount }) => {
          const status = error instanceof ApiError ? error.status : undefined;
          if (status !== undefined && status >= 400 && status < 500) return;
          if (retryCount >= COLD_START_RETRY_COUNT) return;
          setTimeout(() => revalidate({ retryCount }), COLD_START_RETRY_INTERVAL_MS);
        },
      }}
    >
      <ThemeProvider>
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </SWRConfig>
  );
}
