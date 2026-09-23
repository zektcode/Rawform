import type { AnalysisResult } from "@/lib/types";
import { Panel, Stat } from "@/components/ui";
import TimeSeries from "@/components/charts/TimeSeries";
import { formatHz, formatPct } from "@/lib/format";

export default function StereoTab({ result, currentTime }: { result: AnalysisResult; currentTime: number }) {
  const s = result.stereo;

  if (!s.is_stereo) {
    return (
      <Panel>
        <p className="text-[12px] text-rf-text-dim">File is mono — stereo-specific analysis is not applicable.</p>
      </Panel>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 md:gap-4">
        <Panel>
          <Stat label="Phase Correlation" value={s.phase_correlation?.toFixed(2) ?? "—"} tone={s.phase_correlation !== null && s.phase_correlation < 0.3 ? "amber" : "default"} />
        </Panel>
        <Panel>
          <Stat label="L/R Balance" value={s.lr_balance_db?.toFixed(2) ?? "—"} unit="dB" />
        </Panel>
        <Panel>
          <Stat label="Side/Mid Ratio" value={s.side_to_mid_ratio_db?.toFixed(2) ?? "—"} unit="dB" />
        </Panel>
        <Panel>
          <Stat label="Mono Compatible" value={s.mono_compatible === null ? "—" : s.mono_compatible ? "Yes" : "Check"} tone={s.mono_compatible === false ? "amber" : "green"} />
        </Panel>
      </div>

      <Panel title="Phase Correlation Over Time" subtitle="1s windows · +1 mono-safe, 0 wide, -1 out of phase">
        <TimeSeries
          series={[
            {
              time_s: s.correlation_over_time?.time_s || [],
              values: s.correlation_over_time?.correlation || [],
              color: "#4cbd8c",
              name: "Correlation",
            },
          ]}
          yDomain={[-1, 1]}
          currentTime={currentTime}
        />
      </Panel>

      <Panel title="Stereo Width by Frequency Band" subtitle="side-channel energy ratio (higher = wider)">
        <div className="grid grid-cols-4 sm:grid-cols-7 gap-2">
          {(s.width_by_band || []).map((b, i) => (
            <div key={i} className="text-center">
              <div className="h-20 flex items-end justify-center">
                <div
                  className="w-4 bg-rf-blue rounded-sm"
                  style={{ height: `${Math.min(100, b.side_ratio * 200)}%` }}
                />
              </div>
              <div className="text-[9px] text-rf-text-faint font-data mt-1">{formatHz(b.range_hz[0])}</div>
              <div className="text-[9px] text-rf-text-dim font-data">{formatPct(b.side_ratio)}</div>
            </div>
          ))}
        </div>
      </Panel>

      {s.notes.length > 0 && (
        <Panel title="Notes">
          <ul className="text-[12px] text-rf-text-dim space-y-1">
            {s.notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </Panel>
      )}
    </div>
  );
}
