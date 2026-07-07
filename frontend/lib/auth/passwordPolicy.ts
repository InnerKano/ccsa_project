/**
 * Password policy — frontend mirror of backend `modules/auth/password_policy.py`.
 *
 * This drives live UX feedback (strength meter + inline hints). It is NOT a
 * security boundary: the backend re-validates every password and is the source
 * of truth (D24). Keep the two in sync intentionally when the rules change.
 */

export const MIN_LENGTH = 8;
export const MAX_LENGTH = 128;

// Mirror of the backend blocklist (kept small on purpose — Risk #3). Lowercased.
const COMMON_PASSWORDS = new Set<string>([
  "password",
  "password1",
  "password123",
  "passw0rd",
  "12345678",
  "123456789",
  "1234567890",
  "qwerty",
  "qwerty123",
  "qwertyuiop",
  "111111",
  "11111111",
  "abc12345",
  "iloveyou",
  "admin",
  "administrator",
  "welcome",
  "welcome1",
  "letmein",
  "monkey",
  "dragon",
  "sunshine",
  "princess",
  "football",
  "baseball",
  "trustno1",
  "changeme",
  "secret",
  "master",
  "superman",
  "ccsa",
  "ccsa1234",
  "savings",
  "creditcard",
]);

export type PasswordStrength = {
  /** 0 (empty/invalid) … 4 (strong) — drives the meter width and label. */
  score: 0 | 1 | 2 | 3 | 4;
  label: "Too short" | "Weak" | "Fair" | "Good" | "Strong";
  /** Blocking problems (mirror the backend). Empty ⇒ acceptable to submit. */
  issues: string[];
  /** True when no blocking issues remain. */
  acceptable: boolean;
};

/** Hard rules — mirror `password_issues` on the backend (order-aligned). */
export function passwordIssues(password: string, email?: string): string[] {
  const issues: string[] = [];

  if (password.length < MIN_LENGTH) issues.push(`Use at least ${MIN_LENGTH} characters`);
  if (password.length > MAX_LENGTH) issues.push(`Use at most ${MAX_LENGTH} characters`);

  const lowered = password.toLowerCase();
  if (COMMON_PASSWORDS.has(lowered)) {
    issues.push("This password is too common — choose something less predictable");
  }

  if (email) {
    const localPart = email.split("@", 1)[0]?.trim().toLowerCase() ?? "";
    if (localPart && lowered.includes(localPart)) {
      issues.push("Do not include your email in your password");
    }
  }

  const stripped = password.trim();
  if (stripped && new Set(stripped).size === 1) {
    issues.push("Avoid repeating a single character");
  }

  return issues;
}

/**
 * Soft, guidance-only strength estimate (NIST favors length + variety over
 * forced composition). Never blocks beyond the hard `issues` above.
 */
export function evaluatePassword(password: string, email?: string): PasswordStrength {
  const issues = passwordIssues(password, email);
  const acceptable = issues.length === 0;

  if (password.length === 0) {
    return { score: 0, label: "Too short", issues, acceptable: false };
  }
  if (password.length < MIN_LENGTH) {
    return { score: 1, label: "Too short", issues, acceptable: false };
  }

  let points = 0;
  if (password.length >= 12) points += 1;
  if (password.length >= 16) points += 1;
  const variety =
    (/[a-z]/.test(password) ? 1 : 0) +
    (/[A-Z]/.test(password) ? 1 : 0) +
    (/[0-9]/.test(password) ? 1 : 0) +
    (/[^A-Za-z0-9]/.test(password) ? 1 : 0);
  if (variety >= 2) points += 1;
  if (variety >= 3) points += 1;

  // Common/blocked passwords can never read as strong.
  if (!acceptable) {
    return { score: 1, label: "Weak", issues, acceptable };
  }

  const score = Math.min(4, Math.max(1, points)) as 1 | 2 | 3 | 4;
  const label = (["Weak", "Weak", "Fair", "Good", "Strong"] as const)[score];
  return { score, label, issues, acceptable };
}
