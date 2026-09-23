"use client";

import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import { Play, Pause, Volume2, VolumeX, Repeat } from "lucide-react";
import { formatTime } from "@/lib/format";

export interface AudioPlayerHandle {
  seekTo: (seconds: number) => void;
}

interface Marker {
  time_s: number;
  color: "blue" | "red" | "amber";
  label?: string;
}

interface Props {
  src: string;
  duration: number;
  markers?: Marker[];
  onTimeUpdate?: (t: number) => void;
}

const AudioPlayer = forwardRef<AudioPlayerHandle, Props>(function AudioPlayer(
  { src, duration, markers = [], onTimeUpdate },
  ref
) {
  const audioEl = useRef<HTMLAudioElement | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const gainLtoL = useRef<GainNode | null>(null);
  const gainLtoR = useRef<GainNode | null>(null);
  const gainRtoL = useRef<GainNode | null>(null);
  const gainRtoR = useRef<GainNode | null>(null);
  const masterGain = useRef<GainNode | null>(null);

  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [volume, setVolume] = useState(0.85);
  const [muted, setMuted] = useState(false);
  const [mono, setMono] = useState(false);
  const [loop, setLoop] = useState(false);

  useImperativeHandle(ref, () => ({
    seekTo(seconds: number) {
      if (audioEl.current) {
        audioEl.current.currentTime = seconds;
        setCurrentTime(seconds);
        if (!playing) audioEl.current.play().then(() => setPlaying(true)).catch(() => {});
      }
    },
  }));

  // Build the Web Audio graph once, so we can do a real L/R -> mono
  // fold-down for the Stereo/Mono audition toggle rather than faking it.
  useEffect(() => {
    if (!audioEl.current) return;
    const AudioCtx =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    const ctx = new AudioCtx();
    const source = ctx.createMediaElementSource(audioEl.current);
    const splitter = ctx.createChannelSplitter(2);
    const merger = ctx.createChannelMerger(2);
    const lToL = ctx.createGain();
    const lToR = ctx.createGain();
    const rToL = ctx.createGain();
    const rToR = ctx.createGain();
    const master = ctx.createGain();

    source.connect(splitter);
    splitter.connect(lToL, 0);
    splitter.connect(lToR, 0);
    splitter.connect(rToL, 1);
    splitter.connect(rToR, 1);
    lToL.connect(merger, 0, 0);
    lToR.connect(merger, 0, 1);
    rToL.connect(merger, 0, 0);
    rToR.connect(merger, 0, 1);
    merger.connect(master);
    master.connect(ctx.destination);

    ctxRef.current = ctx;
    gainLtoL.current = lToL;
    gainLtoR.current = lToR;
    gainRtoL.current = rToL;
    gainRtoR.current = rToR;
    masterGain.current = master;

    setRouting(false, lToL, lToR, rToL, rToR);
    master.gain.value = volume;

    return () => {
      ctx.close().catch(() => {});
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [src]);

  function setRouting(isMono: boolean, lToL: GainNode, lToR: GainNode, rToL: GainNode, rToR: GainNode) {
    if (isMono) {
      // true L+R fold-down, output identically on both channels
      lToL.gain.value = 0.5;
      rToR.gain.value = 0.5;
      lToR.gain.value = 0.5;
      rToL.gain.value = 0.5;
    } else {
      lToL.gain.value = 1;
      rToR.gain.value = 1;
      lToR.gain.value = 0;
      rToL.gain.value = 0;
    }
  }

  useEffect(() => {
    if (!gainLtoL.current || !gainLtoR.current || !gainRtoL.current || !gainRtoR.current) return;
    setRouting(mono, gainLtoL.current, gainLtoR.current, gainRtoL.current, gainRtoR.current);
  }, [mono]);

  useEffect(() => {
    if (masterGain.current) masterGain.current.gain.value = muted ? 0 : volume;
  }, [volume, muted]);

  useEffect(() => {
    const el = audioEl.current;
    if (!el) return;
    const onTime = () => {
      setCurrentTime(el.currentTime);
      onTimeUpdate?.(el.currentTime);
    };
    const onEnded = () => setPlaying(false);
    el.addEventListener("timeupdate", onTime);
    el.addEventListener("ended", onEnded);
    return () => {
      el.removeEventListener("timeupdate", onTime);
      el.removeEventListener("ended", onEnded);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function togglePlay() {
    const el = audioEl.current;
    if (!el) return;
    ctxRef.current?.resume();
    if (playing) {
      el.pause();
      setPlaying(false);
    } else {
      el.play().then(() => setPlaying(true)).catch(() => {});
    }
  }

  function handleSeek(e: React.MouseEvent<HTMLDivElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
    const t = pct * duration;
    if (audioEl.current) {
      audioEl.current.currentTime = t;
      setCurrentTime(t);
    }
  }

  const pct = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="border border-rf-border bg-rf-bg-1 px-4 py-3">
      <audio ref={audioEl} src={src} loop={loop} preload="metadata" crossOrigin="anonymous" />
      <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-3">
        <div className="flex items-center gap-2 md:gap-3 w-full md:flex-1 min-w-0">
          <button
            onClick={togglePlay}
            className="w-8 h-8 flex items-center justify-center rounded-sm bg-rf-blue text-rf-bg-0 shrink-0 hover:bg-rf-blue/90"
          >
            {playing ? <Pause size={14} fill="currentColor" /> : <Play size={14} fill="currentColor" className="ml-0.5" />}
          </button>

          <span className="font-data text-[11px] text-rf-text-dim w-9 text-right shrink-0">{formatTime(currentTime)}</span>

          <div onClick={handleSeek} className="relative flex-1 h-6 flex items-center cursor-pointer group min-w-0">
            <div className="absolute inset-x-0 h-1 bg-rf-bg-3 rounded-full" />
            <div className="absolute h-1 bg-rf-blue rounded-full" style={{ width: `${pct}%` }} />
            <div className="absolute w-2.5 h-2.5 rounded-full bg-rf-text -ml-1.25 shadow" style={{ left: `${pct}%` }} />
            {markers.map((m, i) => {
              const mp = duration > 0 ? (m.time_s / duration) * 100 : 0;
              const color = { blue: "bg-rf-blue", red: "bg-rf-red", amber: "bg-rf-amber" }[m.color];
              return <div key={i} title={m.label} className={`absolute top-0 w-0.5 h-2 ${color}`} style={{ left: `${mp}%` }} />;
            })}
          </div>

          <span className="font-data text-[11px] text-rf-text-faint w-9 shrink-0">{formatTime(duration)}</span>
        </div>

        <div className="flex items-center gap-1.5 justify-end md:justify-start shrink-0">
          <button
            onClick={() => setLoop((l) => !l)}
            title="Loop"
            className={`w-7 h-7 flex items-center justify-center rounded-sm shrink-0 ${loop ? "text-rf-blue" : "text-rf-text-faint hover:text-rf-text-dim"}`}
          >
            <Repeat size={14} />
          </button>

          <button
            onClick={() => setMuted((m) => !m)}
            className="w-7 h-7 flex items-center justify-center rounded-sm text-rf-text-dim hover:text-rf-text shrink-0"
          >
            {muted || volume === 0 ? <VolumeX size={14} /> : <Volume2 size={14} />}
          </button>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={volume}
            onChange={(e) => setVolume(parseFloat(e.target.value))}
            className="w-12 md:w-16 accent-rf-blue shrink-0"
          />

          <div className="flex border border-rf-border rounded-sm overflow-hidden shrink-0 ml-1">
            <button
              onClick={() => setMono(false)}
              className={`px-2 py-1 text-[10px] font-data uppercase ${!mono ? "bg-rf-blue text-rf-bg-0" : "text-rf-text-dim hover:text-rf-text"}`}
            >
              Stereo
            </button>
            <button
              onClick={() => setMono(true)}
              className={`px-2 py-1 text-[10px] font-data uppercase ${mono ? "bg-rf-blue text-rf-bg-0" : "text-rf-text-dim hover:text-rf-text"}`}
            >
              Mono
            </button>
          </div>
        </div>
      </div>
    </div>
  );
});

export default AudioPlayer;
