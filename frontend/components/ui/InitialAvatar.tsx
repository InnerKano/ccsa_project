import { cn } from "@/lib/cn";

/** First alphanumeric character, upper-cased. Falls back to "?" if none. */
function initialOf(label: string): string {
  const match = label.match(/[a-zA-Z0-9]/);
  return match ? match[0].toUpperCase() : "?";
}

type InitialAvatarProps = {
  /** Entity name the initial is derived from (e.g. a merchant). */
  label: string;
  className?: string;
};

/**
 * Circular placeholder showing an entity's initial — a SaaS avatar pattern used
 * to anchor list rows and improve vertical scanning. Decorative (`aria-hidden`):
 * the adjacent text already names the entity for assistive tech.
 */
export function InitialAvatar({ label, className }: InitialAvatarProps) {
  return (
    <span
      className={cn(
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border bg-surface-muted text-sm font-semibold text-foreground",
        className,
      )}
      aria-hidden
    >
      {initialOf(label)}
    </span>
  );
}
