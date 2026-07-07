"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { GuestOnly } from "@/components/auth/GuestOnly";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { Alert, Button, Field } from "@/components/ui";
import { forgotPassword } from "@/lib/api/auth";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);

    if (!email.trim()) {
      setError("Email is required");
      return;
    }

    setLoading(true);
    try {
      const result = await forgotPassword(email);
      // The response is intentionally identical whether or not the account
      // exists (no enumeration, D23) — we surface it as-is.
      setMessage(result.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send the reset link");
    } finally {
      setLoading(false);
    }
  }

  return (
    <GuestOnly>
      <AuthLayout
        title="Reset your password"
        subtitle="Enter your email and we'll send you a link to set a new password."
        footer={
          <>
            Remembered it?{" "}
            <Link href="/login" className="font-medium text-brand-700 hover:text-brand-800">
              Back to sign in
            </Link>
          </>
        }
      >
        {message ? (
          <Alert variant="success">{message}</Alert>
        ) : (
          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <Field
              label="Email"
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            {error && <Alert variant="error">{error}</Alert>}
            <Button type="submit" className="w-full" loading={loading}>
              Send reset link
            </Button>
          </form>
        )}
      </AuthLayout>
    </GuestOnly>
  );
}
