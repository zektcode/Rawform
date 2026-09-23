import type { AnalysisResult } from "@/lib/types";
import { Panel, Stat } from "@/components/ui";
import SpectrumLine from "@/components/charts/SpectrumLine";
import BandBars from "@/components/charts/BandBars";
import { formatHz } from "@/lib/format";

export default function SpectrumTab({ result }: { result: AnalysisResult }) {
  const s = result.spectrum;
  return (
    <div className="space-y-4">
      <Panel title="Averaged Spectrum" subtitle="20Hz–20kHz · log scale">
        <SpectrumLine
          frequencies={s.averaged_spectrum?.frequencies_hz || []}
          magnitudes={s.averaged_spectrum?.magnitude_db || []}
        />
      </Panel>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 md:gap-4">
        <Panel>
          <Stat label="Spectral Centroid" value={formatHz(s.spectral_centroid_hz)} />
        </Panel>
        <Panel>
          <Stat label="Spectral Rolloff (85%)" value={formatHz(s.spectral_rolloff_hz)} />
        </Panel>
        <Panel>
          <Stat label="Spectral Flatness" value={s.spectral_flatness?.toFixed(3) ?? "—"} />
        </Panel>
        <Panel>
          <Stat label="Spectral Slope" value={s.spectral_slope !== null ? `${s.spectral_slope.toFixed(2)} dB/oct` : "—"} />
        </Panel>
      </div>

      <Panel title="Band Energy" subtitle="relative energy per band">
        <BandBars bands={s.bands} valueKey="relative_energy" unit="%" />
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
