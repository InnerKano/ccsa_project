import { API_URL, ApiError, apiFetch } from "@/lib/api/client";
import { getToken } from "@/lib/auth/session";


/**
 *  Download an analysis as a CSV file. Bypasses the apiFetch because the body is text/csv and not JSON.
 */
export async function exportAnalysisCsv(analysisId: string): Promise<void> {
    const headers: Record<string, string> = {};
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;

    const response = await fetch(`${API_URL}/api/analysis/${analysisId}/export.csv`, {
        method: "GET",
        headers,
    });

    if (!response.ok) {
        let message = "Request failed";
        try {
            const data = await response.json();
            if (typeof data?.detail === "string") message = data.detail;
        } catch (error) {
            /** ignore non-JSON errors bodies*/
        }
        throw new ApiError(response.status, message);
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `analysis-${analysisId}.csv`;
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
}