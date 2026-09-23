import type { AnalysisRecord, ComparisonResult, GenreOption } from "./types";

// Auto-detect the backend host. If NEXT_PUBLIC_API_BASE is set, use it.
// Otherwise, assume the backend runs on the same machine/host as the
// frontend on port 8000 — this is what makes "open this on my phone via
// my laptop's LAN IP" work without any config, since the phone's browser
// will hit http://<laptop-lan-ip>:8000 instead of a hardcoded localhost
// (which on the phone would mean the phone itself).
function resolveApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE;
  if (configured) return configured;
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return "http://localhost:8000";
}

export const API_BASE = resolveApiBase();

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) message = body.detail;
    } catch {
      // ignore
    }
    throw new Error(message);
  }
  return res.json();
}

export async function fetchGenres(): Promise<GenreOption[]> {
  const res = await fetch(`${API_BASE}/api/genres`, { cache: "no-store" });
  return handle(res);
}

export async function fetchAnalyses(): Promise<AnalysisRecord[]> {
  const res = await fetch(`${API_BASE}/api/analyses`, { cache: "no-store" });
  return handle(res);
}

export async function fetchAnalysis(id: string): Promise<AnalysisRecord> {
  const res = await fetch(`${API_BASE}/api/analyses/${id}`, { cache: "no-store" });
  return handle(res);
}

export async function uploadTrack(
  file: File,
  genre: string,
  subprofile?: string
): Promise<{ id: string; status: string }> {
  const form = new FormData();
  form.append("file", file);
  form.append("genre", genre);
  if (subprofile) form.append("subprofile", subprofile);
  const res = await fetch(`${API_BASE}/api/analyses`, { method: "POST", body: form });
  return handle(res);
}

export async function uploadReference(
  analysisId: string,
  file: File
): Promise<{ id: string; status: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/analyses/${analysisId}/reference`, {
    method: "POST",
    body: form,
  });
  return handle(res);
}

export async function fetchComparison(analysisId: string, referenceId: string): Promise<ComparisonResult> {
  const res = await fetch(
    `${API_BASE}/api/analyses/${analysisId}/reference/${referenceId}/compare`,
    { cache: "no-store" }
  );
  return handle(res);
}

export async function fetchReferences(analysisId: string): Promise<
  { id: string; filename: string; status: string; progress_pct: number; created_at: string }[]
> {
  const res = await fetch(`${API_BASE}/api/analyses/${analysisId}/references`, { cache: "no-store" });
  return handle(res);
}

export async function deleteAnalysis(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/analyses/${id}`, { method: "DELETE" });
  await handle(res);
}

export function audioUrl(id: string): string {
  return `${API_BASE}/api/analyses/${id}/audio`;
}

export function reportUrl(id: string): string {
  return `${API_BASE}/api/analyses/${id}/report`;
}
