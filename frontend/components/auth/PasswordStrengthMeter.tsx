"use client";

import { cn } from "@/lib/cn";
import { evaluatePassword } from "@/lib/auth/passwordPolicy";

/** Color per strength score — paired with a text label so color is never the
 *  only signal (DESIGN.md §2.1, accessibility). Uses semantic tokens only. */
const SEGMENT_COLOR: Record<number, string> = {
  1: "bg-danger",
  2: "bg-warning",
  3: "bg-brand-500",
  4: "bg-success",
};

/**
 * Guidance-only password strength meter (NIST-aligned, D24). Shows a 4-segment
 * bar, a label, and the first blocking issue as a hint. It never blocks on its
 * own — the form gates submission via `evaluatePassword().acceptable`.
 */
export function PasswordStrengthMeter({
  password,
  email,
  className,
}: {
  password: string;
  email?: string;
  className?: string;
}) {
  if (!password) return null;

  const { score, label, issues } = evaluatePassword(password, email);

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex gap-1" aria-hidden>
        {[1, 2, 3, 4].map((segment) => (
          <span
            key={segment}
            className={cn(
              "h-1.5 flex-1 rounded-full transition-colors",
              segment <= score ? SEGMENT_COLOR[score] : "bg-surface-muted",
            )}
          />
        ))}
      </div>
      <p className="text-xs text-muted" aria-live="polite">
        Password strength: <span className="font-medium text-foreground">{label}</span>
        {issues.length > 0 && <span className="text-muted"> — {issues[0]}</span>}
      </p>
    </div>
  );
}
