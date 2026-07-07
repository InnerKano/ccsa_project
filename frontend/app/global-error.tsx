"use client";

/**
 * Root-layout error boundary. Replaces the whole document when an error is
 * thrown in the root layout itself, so it must render its own <html>/<body>
 * and cannot rely on Providers, theme tokens, or the design system.
 */
import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[CCSA] global error:", error);
  }, [error]);

  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: "100dvh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
          background: "#f8fafc",
          color: "#0f172a",
          padding: "1rem",
        }}
      >
        <div style={{ maxWidth: 420, textAlign: "center" }}>
          <h1 style={{ fontSize: "1.125rem", fontWeight: 600, margin: "0 0 0.5rem" }}>
            Something went wrong
          </h1>
          <p style={{ fontSize: "0.875rem", color: "#64748b", margin: "0 0 1rem" }}>
            The app hit a temporary error. Please try again.
          </p>
          {error?.digest && (
            <p style={{ fontSize: "0.75rem", color: "#94a3b8", margin: "0 0 1rem" }}>
              Reference: {error.digest}
            </p>
          )}
          <button
            type="button"
            onClick={reset}
            style={{
              height: 44,
              padding: "0 1.25rem",
              borderRadius: 8,
              border: "none",
              background: "#4f46e5",
              color: "#fff",
              fontSize: "0.875rem",
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
