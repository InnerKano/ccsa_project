"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";

import { GuestOnly } from "@/components/auth/GuestOnly";
import { PasswordField } from "@/components/auth/PasswordField";
import { PasswordStrengthMeter } from "@/components/auth/PasswordStrengthMeter";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { Alert, Button, Spinner, buttonClass } from "@/components/ui";
import { resetPassword } from "@/lib/api/auth";
import { evaluatePassword } from "@/lib/auth/passwordPolicy";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  if (!token) {
    return (
      <div className="space-y-4">
        <Alert variant="error">
          This reset link is missing or invalid. Request a new one to continue.
        </Alert>
        <Link href="/forgot-password" className={`${buttonClass("primary")} w-full`}>
          Request a new link
        </Link>
      </div>
    );
  }

  if (done) {
    return (
      <div className="space-y-4">
        <Alert variant="success">
          Your password has been reset. Sign in with your new password.
        </Alert>
        <Link href="/login" className={`${buttonClass("primary")} w-full`}>
          Go to sign in
        </Link>
      </div>
    );
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    const { acceptable, issues } = evaluatePassword(password);
    if (!acceptable) {
      setError(issues[0] ?? "Please choose a stronger password");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      await resetPassword(token, password);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reset your password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <div className="space-y-2">
        <PasswordField
          label="New password"
          id="password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          hint="At least 8 characters. Longer passphrases are stronger."
        />
        <PasswordStrengthMeter password={password} />
      </div>
      <PasswordField
        label="Confirm new password"
        id="confirm-password"
        autoComplete="new-password"
        value={confirm}
        onChange={(e) => setConfirm(e.target.value)}
        error={confirm && password !== confirm ? "Passwords do not match" : undefined}
      />
      {error && <Alert variant="error">{error}</Alert>}
      <Button type="submit" className="w-full" loading={loading}>
        Reset password
      </Button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <GuestOnly>
      <AuthLayout
        title="Set a new password"
        subtitle="Choose a strong password you don't use elsewhere."
        footer={
          <Link href="/login" className="font-medium text-brand-700 hover:text-brand-800">
            Back to sign in
          </Link>
        }
      >
        <Suspense
          fallback={
            <div className="flex justify-center py-6" role="status" aria-label="Loading">
              <Spinner size={24} />
            </div>
          }
        >
          <ResetPasswordForm />
        </Suspense>
      </AuthLayout>
    </GuestOnly>
  );
}
