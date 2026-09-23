# Rawform — Techno & Psytrance Mix Analysis (V1)

Rawform analyzes your own uploaded Techno or Psytrance track and returns real,
measurement-backed mix feedback: loudness, dynamics, spectral balance, low-end
and kick/bass interaction, stereo/mono compatibility, clipping, resonances,
and evidence-backed findings with a technical "Mix Health" score.

**Everything runs locally by default.** No audio is uploaded to any external
service. There is no AI-interpretation layer wired in yet (see "Not yet
implemented" below) — V1 is the real DSP engine end to end.

Want this live on the web instead of just localhost? See
**[DEPLOY.md](./DEPLOY.md)** for deploying the frontend to Vercel and the
backend to Railway (or Render/Fly) — a couple of architecture constraints
mean the backend can't run as Vercel serverless functions; DEPLOY.md
explains why and how to do it properly.

---

## 1. Prerequisites

- Python 3.10+ (tested on 3.12)
- Node.js 18+ (tested on 22)
- `ffmpeg` on your PATH (used as a decode fallback for unusual files, and for MP3)

## 2. Installation

```bash
# from the project root
pip install --break-system-packages -r backend/requirements.txt
cd frontend && npm install && cd ..
```

## 3. Environment variables

```bash
cp .env.example frontend/.env.local
```

The only variable is `NEXT_PUBLIC_API_BASE`, which tells the frontend where
the backend API is running (defaults to `http://localhost:8000`). The backend
itself needs no environment variables or API keys — the DSP engine has no
external dependencies.

## 4. Starting the backend

```bash
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Or: `make backend`

This creates `backend/rawform.db` (SQLite) and serves the API at
`http://localhost:8000`. Check it's alive: `curl http://localhost:8000/api/health`

## 5. Starting the frontend

In a second terminal:

```bash
cd frontend
npm run dev
```

Or: `make frontend`

Open **http://localhost:3000**

## 6. Uploading a track

1. Go to `http://localhost:3000/new` ("New Analysis" in the sidebar).
2. Drag in a WAV, AIFF, FLAC, or MP3 file (up to 500 MB).
3. Choose **Techno** or **Psytrance**, optionally a subprofile (e.g. Hypnotic,
   Full-On) — this refines interpretation and thresholds, not the core DSP.
4. Click **Analyze Track**. You'll land on the analysis page, which polls the
   backend and shows live progress (loading → metadata → loudness → dynamics
   → spectrum → low_end → kick_bass → stereo → clipping → transients →
   resonances → findings) until it's done — usually well under a minute for a
   typical track on a normal machine.

## 7. Running analysis / reading results

Once complete, the analysis screen has: an audio player (with a real
Stereo/Mono fold-down toggle via the Web Audio API, not a cosmetic switch),
and tabs — Overview, Spectrum, Low End, Kick/Bass, Dynamics, Stereo,
Loudness, Timeline, Findings, Reference. Every finding shows its evidence,
an explanation of why it might matter, concrete things to try, a confidence
score, and (where applicable) a "Jump to timestamp" button that seeks the
player.

## 8. Reference comparison

From the analysis screen, open the **Reference** tab: upload a second track to compare against (loudness, true peak, crest factor, phase correlation, side/mid ratio, and per-band spectral energy, shown as a diff table and a band-difference chart). You can upload more than one reference and switch between them with the dropdown. Nothing is assumed to be "correct" — it's framed purely as a difference for you to interpret.

## 9. Exporting a report

Click **Report** next to the Mix Health score on the analysis screen. It opens a self-contained, printable HTML report (Track Info, Loudness, Dynamics, Low End, Kick/Bass, Stereo, Clipping, Findings) in a new tab — use the browser's **Print → Save as PDF** for a PDF copy.

## 10. Running tests

```bash
python3 -m pytest tests/ -v
```

23 unit tests run against **programmatically generated synthetic signals**
(sine waves, a synthetic kick impulse, bass tones, a clipped signal,
phase-inverted stereo, broadband noise, and a synthetic kick/bass rhythmic
pattern with overlapping vs. sidechain-ducked variants) — see
`tests/synth.py` and `tests/test_dsp.py`. All 23 currently pass.

---

## What's real vs. heuristic vs. not implemented

### Objective / directly measured
- Sample rate, bit depth, channels, duration, file format (from the decoded file)
- Integrated / momentary / short-term LUFS, RMS, sample peak, true peak (BS.1770 via `pyloudnorm`, true peak via 4x oversampling)
- Crest factor, RMS-over-time
- FFT/STFT band energy (14 bands, 20Hz-20kHz), spectral centroid/rolloff/flatness/slope/flux
- Stereo L/R RMS, phase correlation, Mid/Side energy, width-by-band
- Digital clipping (consecutive near-full-scale samples)

### Heuristic, with an explicit confidence value
- BPM and musical key (never invented — returns "Not confidently detected" below a threshold; see `audio_engine/tempo_key.py`)
- Kick onset detection and kick/bass temporal & frequency overlap (`audio_engine/kick_bass.py`) — confidence derives from onset-strength consistency and detected kick count
- Resonance candidates (narrow-band peaks above a smoothed local baseline)
- All findings in the Findings tab: each has a `confidence` (0-1) and `severity`, is tied to a specific measured value, and is phrased as "potential"/"may indicate" — never a certainty

### Not yet implemented in V1 (by design, per spec)
- **AI interpretation layer** (executive summary / priority areas / production experiments from an LLM reading the structured analysis) — the DSP + findings engine this would sit on top of is complete, but the layer itself isn't wired in
- **Section/timeline auto-detection** (intro/buildup/drop/breakdown labeling) — the Timeline tab shows real synchronized measurement-over-time charts, but doesn't yet auto-label arrangement sections
- Authentication, projects/history persistence beyond the local SQLite list, VST3/AU/desktop/cloud/stem analysis — explicitly out of scope for V1 per spec

---

## Architecture

```
/audio_engine     — pure Python DSP engine, no web framework dependency.
                     Reusable later by a VST3/desktop/CLI consumer.
  loader.py        decode/validate (soundfile + ffmpeg fallback)
  loudness.py      BS.1770 LUFS, true peak
  dynamics.py      crest factor, RMS-over-time
  spectrum.py      STFT, band energy, spectral descriptors
  low_end.py       sub/bass/low-mid analysis, LF stereo correlation
  kick_bass.py     kick onset detection, kick/bass overlap
  stereo.py        phase correlation, M/S, width-by-band
  clipping.py      clipping detection
  transients.py    broadband transient detection
  resonances.py    narrow-band resonance candidates
  tempo_key.py     BPM/key with confidence
  metadata.py      file/track metadata assembly
  findings_engine.py   measurements -> evidence-backed findings
  scoring.py       findings -> Mix Health score (config/scoring.json)
  pipeline.py      orchestrates the full run

/config/profiles   techno.json, psytrance.json — editable thresholds/subprofiles
/config/scoring.json   editable Mix Health weights

/backend           FastAPI app, SQLite job tracking, threaded background
                    analysis (no Redis needed for local V1), report generation

/frontend          Next.js + TypeScript + Tailwind. Dashboard, upload,
                    9-tab analysis screen, real Web Audio mono/stereo player

/tests             23 pytest unit tests against synthetic signals
```

## Recommended next development step

Add the optional AI interpretation layer on top of the existing structured
`findings` / `recommendations` JSON — it should read that structured data
rather than raw audio, per spec (executive summary, priority areas,
explanation, and production experiments, clearly distinguishing
measurement → interpretation → suggestion). After that: arrangement
section auto-detection (intro/buildup/drop/breakdown) for the Timeline tab.
