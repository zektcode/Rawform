import type { AnalysisResult } from "@/lib/types";
import { Panel, Stat, ScoreBadge, SeverityPill } from "@/components/ui";
import { formatTime } from "@/lib/format";

const CATEGORY_LABELS: Record<string, string> = {
  low_end: "Low End",
  tonal: "Tonal",
  dynamics: "Dynamics",
  stereo: "Stereo",
  loudness: "Loudness",
  translation: "Translation",
};

export default function OverviewTab({ result, onJump }: { result: AnalysisResult; onJump: (t: number) => void }) {
  const topFindings = [...result.findings]
    .sort((a, b) => {
      const sevOrder = { high: 0, medium: 1, low: 2 };
      return sevOrder[a.severity] - sevOrder[b.severity] || b.confidence - a.confidence;
    })
    .slice(0, 4);

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 md:gap-4">
      <Panel title="Mix Health" className="col-span-2 sm:col-span-1">
        <div className="flex items-baseline gap-1 mb-4">
          <ScoreBadge score={result.mix_health.overall_score} size="lg" />
          <span className="text-[13px] text-rf-text-dim">/ 100</span>
        </div>
        <div className="space-y-2">
          {Object.entries(result.mix_health.category_scores).map(([cat, score]) => (
            <div key={cat} className="flex items-center gap-2">
              <span className="text-[11px] text-rf-text-dim w-20 shrink-0">{CATEGORY_LABELS[cat] || cat}</span>
              <div className="flex-1 h-1.5 bg-rf-bg-2 rounded-full overflow-hidden">
                <div
                  className={`h-full ${score >= 80 ? "bg-rf-green" : score >= 60 ? "bg-rf-amber" : "bg-rf-red"}`}
                  style={{ width: `${score}%` }}
                />
              </div>
              <span className="text-[11px] font-data text-rf-text-dim w-7 text-right">{score}</span>
            </div>
          ))}
        </div>
        <p className="text-[10.5px] text-rf-text-faint mt-4 leading-relaxed">{result.mix_health.methodology_note}</p>
      </Panel>

      <Panel title="Key Measurements" className="col-span-2">
        <div className="grid grid-cols-2 gap-y-4">
          <Stat label="Integrated LUFS" value={result.loudness.integrated_lufs?.toFixed(1) ?? "—"} unit="LUFS" />
          <Stat label="True Peak" value={result.loudness.true_peak_dbtp?.toFixed(2) ?? "—"} unit="dBTP" />
          <Stat label="Crest Factor" value={result.dynamics.crest_factor_db?.toFixed(1) ?? "—"} unit="dB" />
          <Stat label="Phase Correlation" value={result.stereo.phase_correlation?.toFixed(2) ?? "—"} />
          <Stat label="Sub Energy (20-40Hz)" value={result.low_end.sub_energy_relative !== null ? `${(result.low_end.sub_energy_relative * 100).toFixed(0)}%` : "—"} />
          <Stat label="Kicks Detected" value={String(result.kick_bass.kick_count)} />
          <Stat label="Clipping" value={result.clipping.clipping_detected ? `${result.clipping.clipped_sample_count} samples` : "None detected"} tone={result.clipping.clipping_detected ? "red" : "green"} />
          <Stat label="Mono Compatible" value={result.stereo.mono_compatible === null ? "—" : result.stereo.mono_compatible ? "Yes" : "Check"} tone={result.stereo.mono_compatible === false ? "amber" : "default"} />
        </div>
      </Panel>

      <Panel title="Priority Findings" className="col-span-2">
        {topFindings.length === 0 ? (
          <p className="text-[12px] text-rf-text-dim">No findings above threshold were raised for this track.</p>
        ) : (
          <div className="space-y-3">
            {topFindings.map((f, i) => (
              <div key={i} className="flex items-start justify-between gap-3 pb-3 border-b border-rf-border-soft last:border-b-0 last:pb-0">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <SeverityPill severity={f.severity} />
                    <span className="text-[13px] text-rf-text">{f.title}</span>
                  </div>
                  <p className="text-[11.5px] text-rf-text-dim">{f.explanation}</p>
                </div>
                {f.time_range && (
                  <button onClick={() => onJump(f.time_range![0])} className="shrink-0 text-[11px] text-rf-blue font-data">
                    {formatTime(f.time_range[0])} →
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </Panel>

      <Panel title="Suggested Next Steps" className="col-span-2 sm:col-span-1">
        <ul className="text-[12px] text-rf-text-dim space-y-1.5 list-disc list-inside">
          {result.recommendations.slice(0, 6).map((r, i) => (
            <li key={i}>{r}</li>
          ))}
          {result.recommendations.length === 0 && <li>No specific recommendations were triggered.</li>}
        </ul>
      </Panel>

      <Panel title="Disclaimers" className="col-span-2 sm:col-span-3">
        <ul className="text-[11px] text-rf-text-faint space-y-1">
          {result.disclaimers.map((d, i) => (
            <li key={i}>{d}</li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
