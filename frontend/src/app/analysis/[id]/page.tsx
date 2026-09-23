"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { fetchAnalysis, audioUrl, reportUrl } from "@/lib/api";
import type { AnalysisRecord } from "@/lib/types";
import { ScoreBadge, StatusPill, Button } from "@/components/ui";
import AudioPlayer, { AudioPlayerHandle } from "@/components/AudioPlayer";
import { formatTime } from "@/lib/format";
import { Download } from "lucide-react";

import OverviewTab from "./tabs/OverviewTab";
import SpectrumTab from "./tabs/SpectrumTab";
import LowEndTab from "./tabs/LowEndTab";
import KickBassTab from "./tabs/KickBassTab";
import DynamicsTab from "./tabs/DynamicsTab";
import StereoTab from "./tabs/StereoTab";
import LoudnessTab from "./tabs/LoudnessTab";
import TimelineTab from "./tabs/TimelineTab";
import FindingsTab from "./tabs/FindingsTab";
import ReferenceTab from "./tabs/ReferenceTab";

const TABS = ["Overview", "Spectrum", "Low End", "Kick/Bass", "Dynamics", "Stereo", "Loudness", "Timeline", "Findings", "Reference"] as const;
type Tab = (typeof TABS)[number];

export default function AnalysisPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [record, setRecord] = useState<AnalysisRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("Overview");
  const [playerTime, setPlayerTime] = useState(0);
  const playerRef = useRef<AudioPlayerHandle>(null);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;

    const poll = () => {
      fetchAnalysis(id)
        .then((data) => {
          if (!active) return;
          setRecord(data);
          if (data.status === "pending" || data.status === "processing") {
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
  }, [id]);

  function jumpTo(t: number) {
    playerRef.current?.seekTo(t);
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-10 text-[13px] text-rf-red">
        Could not load this analysis: {error}
      </div>
    );
  }

  if (!record) {
    return <div className="max-w-4xl mx-auto px-6 py-10 text-[13px] text-rf-text-dim">Loading…</div>;
  }

  if (record.status !== "complete") {
    return (
      <div className="max-w-2xl mx-auto px-6 py-16">
        <h1 className="text-[16px] text-rf-text mb-1">{record.filename}</h1>
        <div className="mb-6">
          <StatusPill status={record.status} />
        </div>
        {record.status === "failed" ? (
          <div className="border border-rf-red-dim bg-rf-red-dim/10 text-rf-red text-[13px] px-4 py-3 rounded-sm">
            {record.error_message || "Analysis failed."}
          </div>
        ) : (
          <div>
            <div className="h-1.5 bg-rf-bg-2 rounded-full overflow-hidden mb-2">
              <div
                className="h-full bg-rf-blue transition-all duration-500"
                style={{ width: `${record.progress_pct || 5}%` }}
              />
            </div>
            <div className="text-[12px] text-rf-text-dim font-data">
              {record.progress_stage ? `${record.progress_stage}…` : "Starting…"} ({record.progress_pct || 0}%)
            </div>
          </div>
        )}
      </div>
    );
  }

  const result = record.result!;
  const findingMarkers = result.findings
    .filter((f) => f.time_range)
    .map((f) => ({
      time_s: f.time_range![0],
      color: (f.severity === "high" ? "red" : f.severity === "medium" ? "amber" : "blue") as "red" | "amber" | "blue",
      label: f.title,
    }));

  return (
    <div className="max-w-6xl mx-auto px-6 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start justify-between gap-3 mb-4">
        <div className="min-w-0">
          <h1 className="text-[16px] sm:text-[17px] font-semibold text-rf-text tracking-tight break-words">{result.metadata.filename}</h1>
          <div className="flex items-center gap-x-3 gap-y-1 flex-wrap mt-1.5 text-[11.5px] sm:text-[12px] text-rf-text-dim font-data">
            <span className="capitalize">{result.genre.display_name} · {result.genre.subprofile_label}</span>
            <span>{formatTime(result.metadata.duration_seconds)}</span>
            <span>{result.metadata.sample_rate / 1000}kHz / {result.metadata.bit_depth ?? "?"}-bit / {result.metadata.channels === 2 ? "Stereo" : "Mono"}</span>
            <span>{result.metadata.bpm ? `${result.metadata.bpm} BPM (${Math.round(result.metadata.bpm_confidence * 100)}%)` : "BPM: not confidently detected"}</span>
            <span>{result.metadata.key ? `${result.metadata.key} (${Math.round(result.metadata.key_confidence * 100)}%)` : "Key: not confidently detected"}</span>
          </div>
        </div>
        <div className="text-right shrink-0 self-start sm:self-auto">
          <div className="text-[10px] text-rf-text-faint uppercase tracking-wide mb-0.5">Mix Health</div>
          <ScoreBadge score={result.mix_health.overall_score} size="lg" />
          <span className="text-[13px] text-rf-text-dim">/100</span>
          <div className="mt-2">
            <a href={reportUrl(id)} target="_blank" rel="noreferrer">
              <Button variant="secondary" className="text-[11px] px-2.5 py-1.5">
                <span className="flex items-center gap-1.5">
                  <Download size={12} /> Report
                </span>
              </Button>
            </a>
          </div>
        </div>
      </div>

      {/* Audio player */}
      <div className="mb-5">
        <AudioPlayer
          ref={playerRef}
          src={audioUrl(id)}
          duration={result.metadata.duration_seconds}
          markers={findingMarkers}
          onTimeUpdate={setPlayerTime}
        />
      </div>

      {/* Tabs */}
      <div className="flex border-b border-rf-border mb-5 overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3.5 py-2 text-[12.5px] whitespace-nowrap border-b-2 -mb-px transition-colors ${
              tab === t ? "border-rf-blue text-rf-text" : "border-transparent text-rf-text-dim hover:text-rf-text"
            }`}
          >
            {t}
            {t === "Findings" && result.findings.length > 0 && (
              <span className="ml-1.5 text-[10px] text-rf-text-faint">({result.findings.length})</span>
            )}
          </button>
        ))}
      </div>

      {tab === "Overview" && <OverviewTab result={result} onJump={jumpTo} />}
      {tab === "Spectrum" && <SpectrumTab result={result} />}
      {tab === "Low End" && <LowEndTab result={result} />}
      {tab === "Kick/Bass" && <KickBassTab result={result} onJump={jumpTo} />}
      {tab === "Dynamics" && <DynamicsTab result={result} currentTime={playerTime} />}
      {tab === "Stereo" && <StereoTab result={result} currentTime={playerTime} />}
      {tab === "Loudness" && <LoudnessTab result={result} currentTime={playerTime} />}
      {tab === "Timeline" && <TimelineTab result={result} currentTime={playerTime} />}
      {tab === "Findings" && <FindingsTab result={result} onJump={jumpTo} />}
      {tab === "Reference" && <ReferenceTab analysisId={id} />}
    </div>
  );
}
