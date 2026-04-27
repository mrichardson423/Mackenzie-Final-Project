// Tiny fetch wrapper around the FastAPI backend.

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface AIAnalysis {
  summary: string | null;
  triggered_fields: string[] | null;
  reasoning: string | null;
  ruled_out: string | null;
  benign_explanations: string | null;
  confidence: number | null;
  confidence_reasoning: string | null;
  recommended_actions: string[] | null;
}

export interface TriageResult {
  score: number;
  risk_level: RiskLevel;
  triggered_rules: string[];
  log_entry: Record<string, unknown>;
  ai_analysis: AIAnalysis | null;
  ai_error: string | null;
}

export interface UploadResponse {
  threshold: number;
  total_entries: number;
  flagged_count: number;
  results: TriageResult[];
}

const API_BASE = "http://localhost:8000";

export async function uploadLogFile(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    // Try to surface the FastAPI detail message.
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore JSON parse errors and use the default message
    }
    throw new Error(detail);
  }

  return res.json();
}
