import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

type AlertVariant = "error" | "info" | "success";

const variants: Record<AlertVariant, string> = {
  error: "border-danger/30 bg-[var(--color-danger-bg)] text-danger",
  info: "border-border bg-surface-muted text-foreground",
  success: "border-brand-200 bg-[var(--color-success-bg)] text-brand-800",
};

/** Inline status message for form/API feedback. */
export function Alert({
  variant = "info",
  children,
  className,
}: {
  variant?: AlertVariant;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      className={cn("rounded-lg border px-4 py-3 text-sm", variants[variant], className)}
    >
      {children}
    </div>
  );
}
