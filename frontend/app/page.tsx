"use client";

import Link from "next/link";

import { getToken } from "@/lib/api/auth";

export default function HomePage() {
  const token = getToken();

  return (
    <main style={{ maxWidth: 640, margin: "2rem auto", padding: "0 1rem" }}>
      <h1>Credit Card Savings Analyzer</h1>
      {token ? (
        <p>Signed in. Upload and analysis screens ship in Phase A2–A4.</p>
      ) : (
        <p>
          <Link href="/login">Log in</Link> or <Link href="/register">register</Link> to get
          started.
        </p>
      )}
    </main>
  );
}
