"use client";

import { useState } from "react";
import type { AnalysisResult, Severity } from "@/lib/types";
import FindingCard from "@/components/FindingCard";
import { EmptyState } from "@/components/ui";

const SEVERITY_ORDER: Record<Severity, number> = { high: 0, medium: 1, low: 2 };

export default function FindingsTab({ result, onJump }: { result: AnalysisResult; onJump: (t: number) => void }) {
  const [filter, setFilter] = useState<"all" | Severity>("all");

  const findings = [...result.findings]
    .filter((f) => filter === "all" || f.severity === filter)
    .sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity] || b.confidence - a.confidence);

  const counts = {
    high: result.findings.filter((f) => f.severity === "high").length,
    medium: result.findings.filter((f) => f.severity === "medium").length,
    low: result.findings.filter((f) => f.severity === "low").length,
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        {(["all", "high", "medium", "low"] as const).map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-3 py-1.5 text-[11px] border rounded-sm capitalize font-data ${
              filter === s ? "border-rf-blue text-rf-text bg-rf-blue-dim/10" : "border-rf-border text-rf-text-dim hover:text-rf-text"
            }`}
          >
            {s} {s !== "all" && `(${counts[s]})`}
          </button>
        ))}
      </div>

      {findings.length === 0 ? (
        <EmptyState title="No findings in this category." />
      ) : (
        <div className="space-y-3">
          {findings.map((f, i) => (
            <FindingCard key={i} finding={f} onJump={onJump} />
          ))}
        </div>
      )}
    </div>
  );
}
