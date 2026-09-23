import type { AnalysisResult } from "@/lib/types";
import { Panel, Stat } from "@/components/ui";
import BandBars from "@/components/charts/BandBars";
import { formatHz, formatPct } from "@/lib/format";

export default function LowEndTab({ result }: { result: AnalysisResult }) {
  const l = result.low_end;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 md:gap-4">
        <Panel>
          <Stat label="Sub Energy (20-40Hz)" value={formatPct(l.sub_energy_relative)} />
        </Panel>
        <Panel>
          <Stat label="Bass Energy (40-120Hz)" value={formatPct(l.bass_energy_relative)} />
        </Panel>
        <Panel>
          <Stat label="Low-Mid (120-300Hz)" value={formatPct(l.low_mid_energy_relative)} />
        </Panel>
        <Panel>
          <Stat label="Dominant Region" value={l.dominant_region_hz ? `${formatHz(l.dominant_region_hz[0])}–${formatHz(l.dominant_region_hz[1])}` : "—"} />
        </Panel>
      </div>

      <Panel title="Low-End Band Breakdown" subtitle="20Hz–300Hz">
        <BandBars bands={l.bands} valueKey="relative_energy" unit="%" />
      </Panel>

      <div className="grid grid-cols-2 gap-4">
        <Panel title="Stereo / Mono Compatibility">
          <div className="grid grid-cols-2 gap-4">
            <Stat
              label="LF Stereo Correlation"
              value={l.low_frequency_stereo_correlation?.toFixed(2) ?? "—"}
              tone={l.low_frequency_stereo_correlation !== null && l.low_frequency_stereo_correlation < 0.5 ? "amber" : "default"}
            />
            <Stat
              label="Mono Compatible"
              value={l.low_frequency_mono_compatible === null ? "—" : l.low_frequency_mono_compatible ? "Yes" : "Check"}
              tone={l.low_frequency_mono_compatible === false ? "amber" : "green"}
            />
          </div>
        </Panel>
        <Panel title="Energy Consistency">
          <Stat label="Consistency (20-200Hz)" value={l.energy_consistency !== null ? formatPct(l.energy_consistency) : "—"} />
          <p className="text-[11px] text-rf-text-faint mt-2">
            Higher = more stable low-end level over time. Lower may reflect arrangement changes or inconsistent takes.
          </p>
        </Panel>
      </div>

      {l.notes.length > 0 && (
        <Panel title="Notes">
          <ul className="text-[12px] text-rf-text-dim space-y-1">
            {l.notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </Panel>
      )}
    </div>
  );
}
