import type { AnalysisResult } from "@/lib/types";
import { Panel, Stat } from "@/components/ui";
import TimeSeries from "@/components/charts/TimeSeries";

export default function LoudnessTab({ result, currentTime }: { result: AnalysisResult; currentTime: number }) {
  const l = result.loudness;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 md:gap-4">
        <Panel>
          <Stat label="Integrated LUFS" value={l.integrated_lufs?.toFixed(2) ?? "—"} unit="LUFS" />
        </Panel>
        <Panel>
          <Stat label="True Peak" value={l.true_peak_dbtp?.toFixed(2) ?? "—"} unit="dBTP" tone={l.true_peak_dbtp !== null && l.true_peak_dbtp > -0.3 ? "red" : "default"} />
        </Panel>
        <Panel>
          <Stat label="Loudness Range" value={l.loudness_range_lu?.toFixed(2) ?? "—"} unit="LU" />
        </Panel>
        <Panel>
          <Stat label="True-Peak Headroom" value={l.true_peak_headroom_db?.toFixed(2) ?? "—"} unit="dB" />
        </Panel>
      </div>

      <Panel title="Loudness Over Time" subtitle="short-term (3s) and momentary (400ms)">
        <TimeSeries
          series={[
            { time_s: l.short_term_lufs_timeseries?.time_s || [], values: l.short_term_lufs_timeseries?.lufs || [], color: "#5b8ef0", name: "Short-term LUFS" },
            { time_s: l.momentary_lufs_timeseries?.time_s || [], values: l.momentary_lufs_timeseries?.lufs || [], color: "#4cbd8c", name: "Momentary LUFS" },
          ]}
          height={220}
          currentTime={currentTime}
        />
      </Panel>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 md:gap-4">
        <Panel>
          <Stat label="RMS" value={l.rms_dbfs?.toFixed(2) ?? "—"} unit="dBFS" />
        </Panel>
        <Panel>
          <Stat label="Sample Peak" value={l.sample_peak_dbfs?.toFixed(2) ?? "—"} unit="dBFS" />
        </Panel>
        <Panel>
          <Stat label="Peak-to-LUFS" value={l.peak_to_lufs_db?.toFixed(2) ?? "—"} unit="dB" />
        </Panel>
      </div>

      {l.findings_notes.length > 0 && (
        <Panel title="Notes">
          <ul className="text-[12px] text-rf-text-dim space-y-1">
            {l.findings_notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </Panel>
      )}

      <Panel title="Note">
        <p className="text-[11.5px] text-rf-text-faint">
          There is no single universal loudness target for Techno/Psytrance — this varies by intent, platform, and subgenre. Use these numbers to check consistency and headroom, not to chase a specific number.
        </p>
      </Panel>
    </div>
  );
}
