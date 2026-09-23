"""
kick_bass.py — kick transient detection and kick/bass frequency & temporal
interaction analysis. This is the highest-priority feature for both Techno
and Psytrance per product spec.

Method (documented so confidence values mean something):
  1. Onset detection on a low-passed (<250Hz) envelope to find kick-like
     transients (librosa.onset.onset_detect on a percussive-emphasized band).
  2. For each detected kick onset, estimate the kick's dominant fundamental
     region via a short-time FFT centered on the transient.
  3. Estimate "bass" as sustained low-frequency energy (40-200Hz) that
     persists between/after kick onsets, via envelope follower.
  4. Overlap = simultaneous energy in a shared frequency region during the
     ~80ms following each kick onset (the window where the kick's body and
     any concurrent bass note would collide).
  5. Confidence is derived from: onset strength consistency, number of kicks
     detected, and signal-to-noise of the low end. Low kick count or weak
     onset clarity -> low confidence, surfaced explicitly.
"""
from __future__ import annotations

import numpy as np
import librosa
from scipy.signal import butter, sosfiltfilt, hilbert


def _lowpass(x: np.ndarray, sr: int, cutoff: float) -> np.ndarray:
    nyq = sr / 2
    sos = butter(4, min(cutoff / nyq, 0.999), btype="low", output="sos")
    return sosfiltfilt(sos, x)


def _bandpass(x: np.ndarray, sr: int, lo: float, hi: float) -> np.ndarray:
    nyq = sr / 2
    lo_n = max(lo / nyq, 1e-5)
    hi_n = min(hi / nyq, 0.999)
    if lo_n >= hi_n:
        return np.zeros_like(x)
    sos = butter(4, [lo_n, hi_n], btype="band", output="sos")
    return sosfiltfilt(sos, x)


def detect_kicks(mono: np.ndarray, sample_rate: int, low_cutoff: float = 200.0):
    """Return kick onset times (s) and per-onset strength, using a low-band
    onset-strength envelope so we bias toward kick drums over hats/percs."""
    low = _lowpass(mono, sample_rate, low_cutoff)
    hop_length = 512
    onset_env = librosa.onset.onset_strength(y=low.astype(np.float32), sr=sample_rate, hop_length=hop_length)
    if len(onset_env) < 4 or np.max(onset_env) <= 0:
        return [], [], onset_env, hop_length
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sample_rate, hop_length=hop_length,
        backtrack=True, pre_max=3, post_max=3, pre_avg=5, post_avg=5, delta=0.15, wait=8,
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sample_rate, hop_length=hop_length)
    strengths = onset_env[onset_frames] if len(onset_frames) else np.array([])
    return onset_times.tolist(), strengths.tolist(), onset_env, hop_length


def estimate_fundamental_region(mono: np.ndarray, sr: int, center_sample: int, window_s: float = 0.06):
    """FFT around a transient to estimate its dominant low-frequency content."""
    half = int(window_s * sr / 2)
    start = max(0, center_sample - half)
    end = min(len(mono), center_sample + half)
    seg = mono[start:end]
    if len(seg) < 64:
        return None
    windowed = seg * np.hanning(len(seg))
    spec = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(seg), 1 / sr)
    low_mask = (freqs >= 25) & (freqs <= 200)
    if not np.any(low_mask) or np.max(spec[low_mask]) <= 0:
        return None
    peak_idx = np.argmax(spec[low_mask])
    peak_freq = freqs[low_mask][peak_idx]
    return float(peak_freq)


def analyze_kick_bass(mono: np.ndarray, sample_rate: int) -> dict:
    result: dict = {
        "kick_count": 0,
        "kick_detection_confidence": 0.0,
        "kick_times_s": [],
        "kick_fundamental_hz_median": None,
        "bass_sustain_relative_energy": None,
        "kick_bass_overlap_events": [],
        "overall_overlap_confidence": 0.0,
        "notes": [],
    }

    if len(mono) < sample_rate * 2:
        result["notes"].append("Track too short for kick/bass analysis (need at least ~2s).")
        return result

    kick_times, strengths, onset_env, hop_length = detect_kicks(mono, sample_rate)
    result["kick_count"] = len(kick_times)
    result["kick_times_s"] = [round(t, 3) for t in kick_times]

    if len(kick_times) < 4:
        result["notes"].append(
            "Too few kick-like transients detected for confident kick/bass interaction analysis."
        )
        result["kick_detection_confidence"] = 0.15 if len(kick_times) else 0.0
        return result

    # Confidence from onset-strength consistency (steadier techno/psy kicks
    # -> more consistent strength -> higher confidence) and count.
    strengths_arr = np.array(strengths)
    strength_cv = float(np.std(strengths_arr) / (np.mean(strengths_arr) + 1e-9))
    count_factor = min(1.0, len(kick_times) / 32.0)
    consistency_factor = max(0.0, 1.0 - min(strength_cv, 1.0))
    result["kick_detection_confidence"] = round(0.4 * count_factor + 0.6 * consistency_factor, 2)

    # Kick fundamental estimate per onset
    fundamentals = []
    for t in kick_times:
        center = int(t * sample_rate)
        f = estimate_fundamental_region(mono, sample_rate, center)
        if f:
            fundamentals.append(f)
    if fundamentals:
        result["kick_fundamental_hz_median"] = round(float(np.median(fundamentals)), 1)

    # Bass sustain: envelope of 40-200Hz band, relative to full-band energy
    bass_band = _bandpass(mono, sample_rate, 40, 200)
    full_energy = np.mean(mono ** 2) + 1e-12
    bass_energy = np.mean(bass_band ** 2)
    result["bass_sustain_relative_energy"] = round(float(bass_energy / full_energy), 4)

    # Overlap: for each kick, check simultaneous energy in 40-120Hz during
    # the 20-100ms window AFTER the onset (kick body + potential bass note
    # sustain colliding). Compare against the track's average bass-band
    # energy to flag events with above-average simultaneous energy.
    bass_env = np.abs(hilbert(_bandpass(mono, sample_rate, 40, 120)))
    avg_bass_env = float(np.mean(bass_env))
    events = []
    for t in kick_times:
        s = int((t + 0.02) * sample_rate)
        e = int((t + 0.10) * sample_rate)
        if e > len(bass_env) or s >= e:
            continue
        window_energy = float(np.mean(bass_env[s:e]))
        if avg_bass_env > 0 and window_energy > 1.4 * avg_bass_env:
            events.append({
                "time_s": round(t, 3),
                "frequency_range_hz": [40, 120],
                "relative_intensity": round(window_energy / avg_bass_env, 2),
            })
    result["kick_bass_overlap_events"] = events[:50]  # cap for payload size

    if events:
        overlap_ratio = len(events) / len(kick_times)
        result["overall_overlap_confidence"] = round(
            min(0.95, result["kick_detection_confidence"] * (0.5 + 0.5 * overlap_ratio)), 2
        )
        if overlap_ratio > 0.3:
            result["notes"].append(
                f"Simultaneous kick + sustained bass-band energy detected in "
                f"{len(events)} of {len(kick_times)} detected kick events. "
                "May indicate kick/bass frequency and/or temporal competition."
            )
    else:
        result["notes"].append(
            "No strong simultaneous kick/bass energy spikes detected — kick and bass "
            "appear reasonably separated in this analysis, but always confirm by ear."
        )

    return result
