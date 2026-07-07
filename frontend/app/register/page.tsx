"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { GuestOnly } from "@/components/auth/GuestOnly";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { Alert, Button, Field } from "@/components/ui";
import { useAuth } from "@/lib/auth/context";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (!email.trim()) {
      setError("Email is required");
      return;
    }
    if (!password) {
      setError("Password is required");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);
    try {
      await register(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <GuestOnly>
      <AuthLayout
        title="Create your account"
        subtitle="Upload a statement and see where your recurring money goes."
        footer={
          <>
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-brand-700 hover:text-brand-800">
              Sign in
            </Link>
          </>
        }
      >
        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          <Field
            label="Email"
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Field
            label="Password"
            id="password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            hint="At least 8 characters"
          />
          {error && <Alert variant="error">{error}</Alert>}
          <Button type="submit" className="w-full" loading={loading}>
            Create account
          </Button>
        </form>
      </AuthLayout>
    </GuestOnly>
  );
}
