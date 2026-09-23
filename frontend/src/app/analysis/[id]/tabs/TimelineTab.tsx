import type { AnalysisResult } from "@/lib/types";
import { Panel } from "@/components/ui";
import TimeSeries from "@/components/charts/TimeSeries";

export default function TimelineTab({ result, currentTime }: { result: AnalysisResult; currentTime: number }) {
  const sot = result.spectrum.spectrum_over_time;

  // Low-end energy over time: average of the first 4 (lowest) band columns per frame.
  let lowEndSeries: { time_s: number[]; values: number[] } = { time_s: [], values: [] };
  if (sot && sot.band_energy_db.length > 0) {
    const lowCols = Math.min(4, sot.band_labels.length);
    lowEndSeries = {
      time_s: sot.time_s,
      values: sot.band_energy_db.map((row) => {
        const vals = row.slice(0, lowCols);
        return vals.reduce((a, b) => a + b, 0) / vals.length;
      }),
    };
  }

  let highEndSeries: { time_s: number[]; values: number[] } = { time_s: [], values: [] };
  if (sot && sot.band_energy_db.length > 0) {
    const n = sot.band_labels.length;
    const highCols = Math.max(0, n - 4);
    highEndSeries = {
      time_s: sot.time_s,
      values: sot.band_energy_db.map((row) => {
        const vals = row.slice(highCols);
        return vals.reduce((a, b) => a + b, 0) / (vals.length || 1);
      }),
    };
  }

  return (
    <div className="space-y-4">
      <Panel title="Loudness (Short-Term)" subtitle="synchronized to playback">
        <TimeSeries
          series={[
            {
              time_s: result.loudness.short_term_lufs_timeseries?.time_s || [],
              values: result.loudness.short_term_lufs_timeseries?.lufs || [],
              color: "#5b8ef0",
              name: "LUFS",
            },
          ]}
          height={150}
          currentTime={currentTime}
        />
      </Panel>

      <Panel title="Low-End Energy" subtitle="avg. of lowest analyzed bands, dB">
        <TimeSeries
          series={[{ time_s: lowEndSeries.time_s, values: lowEndSeries.values, color: "#e0645a", name: "Low-end dB" }]}
          height={150}
          currentTime={currentTime}
        />
      </Panel>

      <Panel title="High-End Energy" subtitle="avg. of highest analyzed bands, dB">
        <TimeSeries
          series={[{ time_s: highEndSeries.time_s, values: highEndSeries.values, color: "#d1a24a", name: "High-end dB" }]}
          height={150}
          currentTime={currentTime}
        />
      </Panel>

      <Panel title="Stereo Width (Correlation)">
        <TimeSeries
          series={[
            {
              time_s: result.stereo.correlation_over_time?.time_s || [],
              values: result.stereo.correlation_over_time?.correlation || [],
              color: "#4cbd8c",
              name: "Correlation",
            },
          ]}
          height={150}
          yDomain={[-1, 1]}
          currentTime={currentTime}
        />
      </Panel>

      <Panel title="Dynamics (RMS)">
        <TimeSeries
          series={[
            {
              time_s: result.dynamics.rms_over_time?.time_s || [],
              values: result.dynamics.rms_over_time?.rms_dbfs || [],
              color: "#8a8a8a",
              name: "RMS dBFS",
            },
          ]}
          height={150}
          currentTime={currentTime}
        />
      </Panel>
    </div>
  );
}
