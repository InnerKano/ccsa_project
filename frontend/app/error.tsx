"use client";

/**
 * Route-level error boundary.
 *
 * Without this, any uncaught client-side exception renders Next.js's raw white
 * "Application error" screen with no recovery. This boundary degrades
 * gracefully (matching the project's graceful-degradation philosophy): it shows
 * a branded, recoverable state and logs the real error to the console so the
 * root cause is visible on-device (client errors are not redacted here).
 */
import Link from "next/link";
import { useEffect } from "react";

import { Button, buttonClass, Card, CardContent, CardTitle } from "@/components/ui";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Flaky mobile networks often fail to fetch a lazy-loaded route chunk. That
    // surfaces as an uncaught error even though nothing is actually broken — a
    // single reload re-fetches the chunk. Guard with a timestamp so we never
    // loop if the chunk is genuinely gone (e.g. after a redeploy).
    const message = error?.message ?? "";
    const isChunkError =
      error?.name === "ChunkLoadError" ||
      /loading chunk|dynamically imported module|importing a module script failed/i.test(message);

    if (isChunkError && typeof window !== "undefined") {
      const key = "ccsa:last-chunk-reload";
      const last = Number(window.sessionStorage.getItem(key) ?? 0);
      if (Date.now() - last > 10_000) {
        window.sessionStorage.setItem(key, String(Date.now()));
        window.location.reload();
        return;
      }
    }

    console.error("[CCSA] client-side error:", error);
  }, [error]);

  return (
    <div className="flex min-h-dvh items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardContent className="space-y-4 text-center">
          <CardTitle>Something went wrong</CardTitle>
          <p className="text-sm text-muted">
            The app hit a temporary error. If you just uploaded a statement, the server may have
            been waking up from idle — please try again in a moment.
          </p>
          {error?.digest && <p className="text-xs text-muted">Reference: {error.digest}</p>}
          <div className="flex flex-col justify-center gap-3 sm:flex-row">
            <Button type="button" onClick={reset}>
              Try again
            </Button>
            <Link href="/dashboard" className={buttonClass("secondary")}>
              Go to dashboard
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
