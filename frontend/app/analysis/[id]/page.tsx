"use client";

import { useParams } from "next/navigation";

import { AnalysisDetailView } from "@/components/analysis/AnalysisDetailView";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";

export default function AnalysisPage() {
  const params = useParams();
  const analysisId = typeof params.id === "string" ? params.id : "";

  return (
    <RequireAuth>
      <AppShell>
        <AnalysisDetailView analysisId={analysisId} />
      </AppShell>
    </RequireAuth>
  );
}
