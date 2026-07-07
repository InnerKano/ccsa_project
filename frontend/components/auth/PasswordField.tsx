"use client";

import { useId, useState, type InputHTMLAttributes, type ReactNode } from "react";

import { cn } from "@/lib/cn";
import { Input } from "@/components/ui";

type PasswordFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label: string;
  hint?: ReactNode;
  error?: string | null;
};

/**
 * Password input with a show/hide toggle — the standard control for any
 * password entry (login, register, reset). Mirrors `Field`'s label/hint/error
 * structure and a11y wiring (DESIGN.md §4), adding a reveal button so users can
 * verify what they typed without weakening the field.
 */
export function PasswordField({
  label,
  hint,
  error,
  id,
  className,
  ...props
}: PasswordFieldProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  const [visible, setVisible] = useState(false);

  return (
    <div className="space-y-1.5">
      <label htmlFor={fieldId} className="block text-sm font-medium text-foreground">
        {label}
      </label>
      <div className="relative">
        <Input
          id={fieldId}
          type={visible ? "text" : "password"}
          aria-invalid={error ? true : undefined}
          className={cn("pr-12", error && "border-danger focus:border-danger", className)}
          {...props}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Hide password" : "Show password"}
          className="absolute inset-y-0 right-0 flex items-center px-3 text-xs font-medium text-muted transition-colors hover:text-foreground"
        >
          {visible ? "Hide" : "Show"}
        </button>
      </div>
      {hint && !error && <p className="text-xs text-muted">{hint}</p>}
      {error && <p className="text-xs text-danger">{error}</p>}
    </div>
  );
}
