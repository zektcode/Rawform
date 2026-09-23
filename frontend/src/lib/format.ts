export function formatTime(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function formatDb(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || !isFinite(value)) return "—";
  return `${value.toFixed(digits)} dB`;
}

export function formatHz(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  if (value >= 1000) return `${(value / 1000).toFixed(value % 1000 === 0 ? 0 : 1)} kHz`;
  return `${Math.round(value)} Hz`;
}

export function formatPct(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function severityColor(severity: "low" | "medium" | "high"): string {
  switch (severity) {
    case "high":
      return "text-rf-red border-rf-red-dim bg-rf-red-dim/10";
    case "medium":
      return "text-rf-amber border-rf-amber/40 bg-rf-amber/10";
    default:
      return "text-rf-blue border-rf-blue-dim bg-rf-blue-dim/10";
  }
}

export function scoreColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return "text-rf-text-dim";
  if (score >= 80) return "text-rf-green";
  if (score >= 60) return "text-rf-amber";
  return "text-rf-red";
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
