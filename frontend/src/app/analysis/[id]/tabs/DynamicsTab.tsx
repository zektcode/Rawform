import type { AnalysisResult } from "@/lib/types";
import { Panel, Stat } from "@/components/ui";
import TimeSeries from "@/components/charts/TimeSeries";

export default function DynamicsTab({ result, currentTime }: { result: AnalysisResult; currentTime: number }) {
  const d = result.dynamics;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 md:gap-4">
        <Panel>
          <Stat label="Crest Factor" value={d.crest_factor_db?.toFixed(2) ?? "—"} unit="dB" />
        </Panel>
        <Panel>
          <Stat label="Dynamic Variation" value={d.dynamic_variation_db?.toFixed(2) ?? "—"} unit="dB" />
        </Panel>
        <Panel>
          <Stat label="Peak-to-RMS" value={d.peak_to_rms_db?.toFixed(2) ?? "—"} unit="dB" />
        </Panel>
      </div>

      <Panel title="RMS Over Time" subtitle="100ms windows">
        <TimeSeries
          series={[
            {
              time_s: d.rms_over_time?.time_s || [],
              values: d.rms_over_time?.rms_dbfs || [],
              color: "#5b8ef0",
              name: "RMS (dBFS)",
            },
          ]}
          currentTime={currentTime}
        />
      </Panel>

      {d.notes.length > 0 && (
        <Panel title="Notes">
          <ul className="text-[12px] text-rf-text-dim space-y-1">
            {d.notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </Panel>
      )}
    </div>
  );
}
