"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchAnalyses } from "@/lib/api";
import type { AnalysisRecord } from "@/lib/types";
import { Button, EmptyState, ScoreBadge, StatusPill } from "@/components/ui";
import { formatTime } from "@/lib/format";
import { Plus } from "lucide-react";

export default function DashboardPage() {
  const [analyses, setAnalyses] = useState<AnalysisRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const load = () => {
      fetchAnalyses()
        .then((data) => active && setAnalyses(data))
        .catch((e) => active && setError(e.message));
    };
    load();
    const interval = setInterval(load, 3000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-[20px] font-semibold text-rf-text tracking-tight">Dashboard</h1>
          <p className="text-[13px] text-rf-text-dim mt-1">
            Techno &amp; Psytrance mix analysis — real measurements from your own tracks.
          </p>
        </div>
        <Link href="/new">
          <Button>
            <span className="flex items-center gap-1.5">
              <Plus size={14} /> New Analysis
            </span>
          </Button>
        </Link>
      </div>

      {error && (
        <div className="border border-rf-red-dim bg-rf-red-dim/10 text-rf-red text-[13px] px-4 py-3 mb-6 rounded-sm">
          Could not reach the analysis backend at localhost:8000 — is it running? ({error})
        </div>
      )}

      {analyses === null && !error && (
        <div className="text-[13px] text-rf-text-dim">Loading…</div>
      )}

      {analyses && analyses.length === 0 && (
        <EmptyState
          title="No analyses yet"
          subtitle="Upload a Techno or Psytrance track to get real measurement-backed mix feedback."
        />
      )}

      {analyses && analyses.length > 0 && (
        <div className="border border-rf-border">
          {/* desktop table */}
          <div className="hidden md:grid grid-cols-[1fr_110px_90px_90px_90px_140px] gap-4 px-4 py-2.5 border-b border-rf-border text-[11px] text-rf-text-dim uppercase tracking-wide">
            <div>Track</div>
            <div>Genre</div>
            <div>Duration</div>
            <div>Mix Health</div>
            <div>Status</div>
            <div>Date</div>
          </div>
          {analyses.map((a) => (
            <Link
              key={a.id}
              href={`/analysis/${a.id}`}
              className="hidden md:grid grid-cols-[1fr_110px_90px_90px_90px_140px] gap-4 px-4 py-3 border-b border-rf-border last:border-b-0 hover:bg-rf-bg-2/50 transition-colors items-center"
            >
              <div className="text-[13px] text-rf-text truncate">{a.filename}</div>
              <div className="text-[12px] text-rf-text-dim capitalize">{a.genre}</div>
              <div className="text-[12px] text-rf-text-dim font-data">
                {a.duration_seconds ? formatTime(a.duration_seconds) : "—"}
              </div>
              <div>
                <ScoreBadge score={a.mix_health_score} size="sm" />
              </div>
              <div>
                <StatusPill status={a.status} />
              </div>
              <div className="text-[12px] text-rf-text-faint font-data">
                {new Date(a.created_at).toLocaleString()}
              </div>
            </Link>
          ))}

          {/* mobile cards */}
          {analyses.map((a) => (
            <Link
              key={a.id + "-m"}
              href={`/analysis/${a.id}`}
              className="md:hidden flex items-center justify-between gap-3 px-4 py-3 border-b border-rf-border last:border-b-0 active:bg-rf-bg-2/50"
            >
              <div className="min-w-0">
                <div className="text-[13px] text-rf-text truncate">{a.filename}</div>
                <div className="flex items-center gap-2 mt-1 text-[11px] text-rf-text-dim">
                  <span className="capitalize">{a.genre}</span>
                  <span>·</span>
                  <span className="font-data">{a.duration_seconds ? formatTime(a.duration_seconds) : "—"}</span>
                  <StatusPill status={a.status} />
                </div>
              </div>
              <ScoreBadge score={a.mix_health_score} size="sm" />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
