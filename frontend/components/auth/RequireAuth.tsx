"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Spinner } from "@/components/ui";
import { useAuth } from "@/lib/auth/context";

/**
 * Client-side route guard for pages that require a JWT.
 * localStorage-backed auth cannot run in Next.js middleware without cookies,
 * so protected routes wrap content with this component (see ARCHITECTURE.md).
 */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-dvh items-center justify-center" role="status" aria-label="Loading">
        <Spinner size={32} />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
