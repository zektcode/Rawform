"use client";

import type { Finding } from "@/lib/types";
import { SeverityPill } from "@/components/ui";
import { formatConfidence, formatHz, formatTime } from "@/lib/format";
import { CornerDownRight } from "lucide-react";

export default function FindingCard({ finding, onJump }: { finding: Finding; onJump?: (t: number) => void }) {
  return (
    <div className="border border-rf-border bg-rf-bg-1">
      <div className="px-4 py-3 border-b border-rf-border-soft flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <SeverityPill severity={finding.severity} />
            <span className="text-[11px] text-rf-text-faint font-data">
              Confidence {formatConfidence(finding.confidence)}
            </span>
          </div>
          <h4 className="text-[14px] text-rf-text font-medium">{finding.title}</h4>
          <div className="text-[11px] text-rf-text-dim font-data mt-1 flex gap-3">
            {finding.frequency_range && (
              <span>
                {formatHz(finding.frequency_range[0])}–{formatHz(finding.frequency_range[1])}
              </span>
            )}
            {finding.time_range && (
              <span>
                {formatTime(finding.time_range[0])}–{formatTime(finding.time_range[1])}
              </span>
            )}
          </div>
        </div>
        {finding.time_range && onJump && (
          <button
            onClick={() => onJump(finding.time_range![0])}
            className="shrink-0 flex items-center gap-1 text-[11px] text-rf-blue border border-rf-blue-dim px-2 py-1 rounded-sm hover:bg-rf-blue-dim/10"
          >
            <CornerDownRight size={12} /> Jump to timestamp
          </button>
        )}
      </div>
      <div className="px-4 py-3 space-y-3">
        <div>
          <div className="text-[10px] text-rf-text-faint uppercase tracking-wide mb-1">Evidence</div>
          <ul className="text-[12px] text-rf-text-dim space-y-0.5">
            {finding.evidence.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </div>
        <div>
          <div className="text-[10px] text-rf-text-faint uppercase tracking-wide mb-1">Why it matters</div>
          <p className="text-[12px] text-rf-text-dim">{finding.explanation}</p>
        </div>
        {finding.recommendations.length > 0 && (
          <div>
            <div className="text-[10px] text-rf-text-faint uppercase tracking-wide mb-1">Try</div>
            <ul className="text-[12px] text-rf-text-dim space-y-0.5 list-disc list-inside">
              {finding.recommendations.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
