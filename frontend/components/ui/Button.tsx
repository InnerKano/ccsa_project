import { forwardRef, type ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";
import { Spinner } from "./Spinner";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md";

const base =
  "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60";

const variants: Record<ButtonVariant, string> = {
  primary: "bg-brand-600 text-white hover:bg-brand-700",
  secondary: "bg-surface text-foreground border border-border hover:bg-surface-muted",
  ghost: "text-brand-700 hover:bg-brand-50",
  danger: "bg-danger text-white hover:opacity-90",
};

const sizes: Record<ButtonSize, string> = {
  sm: "h-9 px-3 text-sm",
  md: "h-11 px-5 text-sm",
};

/** Shared class recipe so `next/link` can render as a styled button too. */
export function buttonClass(variant: ButtonVariant = "primary", size: ButtonSize = "md"): string {
  return cn(base, variants[variant], sizes[size]);
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", size = "md", loading = false, disabled, className, children, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      className={cn(buttonClass(variant, size), className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Spinner size={16} />}
      {children}
    </button>
  );
});
