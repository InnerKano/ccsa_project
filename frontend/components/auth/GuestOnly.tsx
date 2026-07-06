"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Spinner } from "@/components/ui";
import { useAuth } from "@/lib/auth/context";

/** Redirect authenticated users away from login/register to the app hub. */
export function GuestOnly({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-dvh items-center justify-center" role="status" aria-label="Loading">
        <Spinner size={32} />
      </div>
    );
  }

  if (isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
