import type { AnalysisResult } from "@/lib/types";
import { Panel, Stat } from "@/components/ui";
import { formatHz, formatConfidence, formatTime, formatPct } from "@/lib/format";
import { CornerDownRight } from "lucide-react";

export default function KickBassTab({ result, onJump }: { result: AnalysisResult; onJump: (t: number) => void }) {
  const kb = result.kick_bass;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 md:gap-4">
        <Panel>
          <Stat label="Kicks Detected" value={String(kb.kick_count)} />
        </Panel>
        <Panel>
          <Stat label="Kick Detection Confidence" value={formatConfidence(kb.kick_detection_confidence)} />
        </Panel>
        <Panel>
          <Stat label="Kick Fundamental (median)" value={formatHz(kb.kick_fundamental_hz_median)} />
        </Panel>
        <Panel>
          <Stat label="Bass Sustain (rel. energy)" value={formatPct(kb.bass_sustain_relative_energy)} />
        </Panel>
      </div>

      <Panel
        title="Kick/Bass Overlap Events"
        subtitle={`${kb.kick_bass_overlap_events.length} of ${kb.kick_count} kick events flagged`}
      >
        {kb.kick_bass_overlap_events.length === 0 ? (
          <p className="text-[12px] text-rf-text-dim">
            No strong simultaneous kick/bass energy spikes detected in the analyzed 40-120 Hz region.
          </p>
        ) : (
          <div className="divide-y divide-rf-border-soft">
            {kb.kick_bass_overlap_events.map((e, i) => (
              <div key={i} className="flex items-center justify-between py-2">
                <div className="flex items-center gap-4">
                  <span className="font-data text-[12px] text-rf-text w-14">{formatTime(e.time_s)}</span>
                  <span className="font-data text-[11px] text-rf-text-dim">
                    {formatHz(e.frequency_range_hz[0])}–{formatHz(e.frequency_range_hz[1])}
                  </span>
                  <span className="text-[11px] text-rf-text-faint">{e.relative_intensity.toFixed(2)}x baseline</span>
                </div>
                <button
                  onClick={() => onJump(e.time_s)}
                  className="flex items-center gap-1 text-[11px] text-rf-blue hover:underline"
                >
                  <CornerDownRight size={12} /> Jump
                </button>
              </div>
            ))}
          </div>
        )}
      </Panel>

      {kb.notes.length > 0 && (
        <Panel title="Notes">
          <ul className="text-[12px] text-rf-text-dim space-y-1">
            {kb.notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </Panel>
      )}

      <Panel title="Method">
        <p className="text-[11.5px] text-rf-text-faint leading-relaxed">
          Kicks are detected via onset detection on a low-passed (&lt;200Hz) envelope. Overlap events compare
          40-120Hz envelope energy in the 20-100ms window following each kick against the track&apos;s average
          bass-band energy. This is a heuristic, not a certainty — always confirm by soloing the kick and bass.
        </p>
      </Panel>
    </div>
  );
}
