"use client";

import { useEffect, useRef, useState } from "react";
import { fetchReferences, uploadReference, fetchComparison } from "@/lib/api";
import type { ComparisonResult } from "@/lib/types";
import { Panel, Button, StatusPill } from "@/components/ui";
import { formatHz } from "@/lib/format";
import { UploadCloud } from "lucide-react";

interface RefRecord {
  id: string;
  filename: string;
  status: string;
  progress_pct: number;
  created_at: string;
}

function Diff({ value, unit = "" }: { value: number | null; unit?: string }) {
  if (value === null) return <span className="text-rf-text-faint">—</span>;
  const tone = value > 0 ? "text-rf-blue" : value < 0 ? "text-rf-amber" : "text-rf-text-dim";
  const sign = value > 0 ? "+" : "";
  return (
    <span className={`font-data ${tone}`}>
      {sign}
      {value.toFixed(2)}
      {unit}
    </span>
  );
}

export default function ReferenceTab({ analysisId }: { analysisId: string }) {
  const [refs, setRefs] = useState<RefRecord[] | null>(null);
  const [selectedRef, setSelectedRef] = useState<string | null>(null);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const poll = () => {
      fetchReferences(analysisId)
        .then((data) => {
          if (!active) return;
          setRefs(data);
          if (!selectedRef && data.length > 0) setSelectedRef(data[0].id);
          if (data.some((r) => r.status === "pending" || r.status === "processing")) {
            timer = setTimeout(poll, 1500);
          }
        })
        .catch((e) => active && setError(e.message));
    };
    poll();
    return () => {
      active = false;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analysisId]);

  useEffect(() => {
    if (!selectedRef) return;
    const ref = refs?.find((r) => r.id === selectedRef);
    if (!ref || ref.status !== "complete") return;
    fetchComparison(analysisId, selectedRef)
      .then(setComparison)
      .catch((e) => setError(e.message));
  }, [selectedRef, refs, analysisId]);

  async function handleUpload(file: File) {
    setUploading(true);
    setError(null);
    try {
      const res = await uploadReference(analysisId, file);
      setSelectedRef(res.id);
      const data = await fetchReferences(analysisId);
      setRefs(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  const activeRef = refs?.find((r) => r.id === selectedRef);
  const c = activeRef?.status === "complete" ? comparison?.comparison : undefined;

  return (
    <div className="space-y-4">
      <Panel title="Reference Track">
        <div className="flex items-center gap-3 flex-wrap">
          <input
            ref={inputRef}
            type="file"
            accept=".wav,.wave,.aiff,.aif,.flac,.mp3"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleUpload(f);
            }}
          />
          <Button variant="secondary" onClick={() => inputRef.current?.click()} disabled={uploading}>
            <span className="flex items-center gap-1.5">
              <UploadCloud size={14} /> {uploading ? "Uploading…" : "Upload a reference track"}
            </span>
          </Button>

          {refs && refs.length > 0 && (
            <select
              value={selectedRef || ""}
              onChange={(e) => setSelectedRef(e.target.value)}
              className="bg-rf-bg-2 border border-rf-border text-[12px] text-rf-text px-2 py-2 rounded-sm"
            >
              {refs.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.filename}
                </option>
              ))}
            </select>
          )}

          {activeRef && activeRef.status !== "complete" && <StatusPill status={activeRef.status} />}
        </div>
        {error && <p className="text-[12px] text-rf-red mt-3">{error}</p>}
        {!refs?.length && !uploading && (
          <p className="text-[12px] text-rf-text-dim mt-3">
            Upload a track you like the sound of in the same subgenre to compare loudness, dynamics, stereo, and
            spectral balance against your mix. The reference is never assumed to be &quot;correct&quot; — it&apos;s a
            point of comparison.
          </p>
        )}
      </Panel>

      {c && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <Panel title="Your Mix">
              <p className="text-[12px] text-rf-text-dim">{c.your_track.filename}</p>
            </Panel>
            <Panel title="Reference">
              <p className="text-[12px] text-rf-text-dim">{c.reference.filename}</p>
            </Panel>
          </div>

          <Panel title="Loudness & Dynamics">
            <table className="w-full text-[12px]">
              <thead>
                <tr className="text-rf-text-faint text-[10px] uppercase tracking-wide">
                  <td className="pb-2">Metric</td>
                  <td className="pb-2">Your Mix</td>
                  <td className="pb-2">Reference</td>
                  <td className="pb-2">Difference</td>
                </tr>
              </thead>
              <tbody className="font-data">
                <tr className="border-t border-rf-border-soft">
                  <td className="py-2 font-sans text-rf-text-dim">Integrated LUFS</td>
                  <td>{c.loudness.integrated_lufs.your_track ?? "—"}</td>
                  <td>{c.loudness.integrated_lufs.reference ?? "—"}</td>
                  <td>
                    <Diff value={c.loudness.integrated_lufs.difference} unit=" dB" />
                  </td>
                </tr>
                <tr className="border-t border-rf-border-soft">
                  <td className="py-2 font-sans text-rf-text-dim">True Peak</td>
                  <td>{c.loudness.true_peak_dbtp.your_track ?? "—"}</td>
                  <td>{c.loudness.true_peak_dbtp.reference ?? "—"}</td>
                  <td>
                    <Diff value={c.loudness.true_peak_dbtp.difference} unit=" dB" />
                  </td>
                </tr>
                <tr className="border-t border-rf-border-soft">
                  <td className="py-2 font-sans text-rf-text-dim">Crest Factor</td>
                  <td>{c.dynamics.crest_factor_db.your_track ?? "—"}</td>
                  <td>{c.dynamics.crest_factor_db.reference ?? "—"}</td>
                  <td>
                    <Diff value={c.dynamics.crest_factor_db.difference} unit=" dB" />
                  </td>
                </tr>
                <tr className="border-t border-rf-border-soft">
                  <td className="py-2 font-sans text-rf-text-dim">Phase Correlation</td>
                  <td>{c.stereo.phase_correlation.your_track ?? "—"}</td>
                  <td>{c.stereo.phase_correlation.reference ?? "—"}</td>
                  <td>
                    <Diff value={c.stereo.phase_correlation.difference} />
                  </td>
                </tr>
                <tr className="border-t border-rf-border-soft">
                  <td className="py-2 font-sans text-rf-text-dim">Side/Mid Ratio</td>
                  <td>{c.stereo.side_to_mid_ratio_db.your_track ?? "—"}</td>
                  <td>{c.stereo.side_to_mid_ratio_db.reference ?? "—"}</td>
                  <td>
                    <Diff value={c.stereo.side_to_mid_ratio_db.difference} unit=" dB" />
                  </td>
                </tr>
              </tbody>
            </table>
          </Panel>

          <Panel title="Frequency Band Difference" subtitle="your mix vs. reference, dB">
            <div className="space-y-1.5">
              {c.frequency_bands.map((b, i) => {
                const diff = b.difference_db ?? 0;
                const pct = Math.min(50, Math.abs(diff) * 2.5);
                return (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-[10px] text-rf-text-faint font-data w-16 shrink-0">
                      {formatHz(b.range_hz[0])}
                    </span>
                    <div className="flex-1 h-3 relative bg-rf-bg-2 rounded-sm overflow-hidden">
                      <div className="absolute left-1/2 top-0 bottom-0 w-px bg-rf-border" />
                      <div
                        className={`absolute top-0 bottom-0 ${diff >= 0 ? "bg-rf-blue" : "bg-rf-amber"}`}
                        style={
                          diff >= 0
                            ? { left: "50%", width: `${pct}%` }
                            : { right: "50%", width: `${pct}%` }
                        }
                      />
                    </div>
                    <span className="text-[10px] font-data text-rf-text-dim w-14 text-right shrink-0">
                      {diff > 0 ? "+" : ""}
                      {diff.toFixed(1)} dB
                    </span>
                  </div>
                );
              })}
            </div>
            <p className="text-[11px] text-rf-text-faint mt-4">
              Blue = your mix has more energy than the reference in this band. Amber = less. This describes a
              difference — it doesn&apos;t mean the reference is correct or that your mix needs to match it exactly.
            </p>
          </Panel>
        </>
      )}

      {activeRef && activeRef.status !== "complete" && (
        <Panel>
          <p className="text-[12px] text-rf-text-dim">Analyzing reference track…</p>
        </Panel>
      )}
    </div>
  );
}
