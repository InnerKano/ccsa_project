"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { GuestOnly } from "@/components/auth/GuestOnly";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { Alert, Button, Field } from "@/components/ui";
import { useAuth } from "@/lib/auth/context";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <GuestOnly>
      <AuthLayout
        title="Welcome back"
        subtitle="Sign in to review your statements and savings."
        footer={
          <>
            No account?{" "}
            <Link href="/register" className="font-medium text-brand-700 hover:text-brand-800">
              Create one
            </Link>
          </>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Field
            label="Email"
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Field
            label="Password"
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
          {error && <Alert variant="error">{error}</Alert>}
          <Button type="submit" className="w-full" loading={loading}>
            Sign in
          </Button>
        </form>
      </AuthLayout>
    </GuestOnly>
  );
}
