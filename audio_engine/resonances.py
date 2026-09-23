"""
resonances.py — narrow-band spectral peak (resonance) detection.
Finds frequencies where energy significantly and persistently exceeds a
local smoothed baseline — candidates for problematic resonances or
boxiness, not automatically "bad".
"""
from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks
from .spectrum import compute_stft


def analyze_resonances(mono: np.ndarray, sample_rate: int, max_results: int = 8) -> list[dict]:
    if len(mono) < 4096:
        return []

    mag, freqs, times = compute_stft(mono, sample_rate, n_fft=8192, hop_length=2048)
    power = mag ** 2
    avg_power_db = 10 * np.log10(power.mean(axis=1) + 1e-15)

    # Smoothed baseline via a wide moving average (in log-freq space would
    # be more perceptually accurate; we approximate with a wide bin window).
    kernel = max(5, int(len(avg_power_db) * 0.01))
    kernel += (kernel % 2 == 0)
    pad = kernel // 2
    padded = np.pad(avg_power_db, pad, mode="edge")
    baseline = np.convolve(padded, np.ones(kernel) / kernel, mode="valid")

    diff = avg_power_db - baseline
    # Only consider musically relevant range for resonance flags
    valid_mask = (freqs >= 60) & (freqs <= 12000)

    peak_indices, properties = find_peaks(
        np.where(valid_mask, diff, -np.inf), height=4.0, distance=8, prominence=3.0
    )

    findings = []
    # persistence: fraction of time-frames where this bin (± neighbors) is
    # elevated above its own baseline, as a rough confidence proxy.
    for idx in peak_indices:
        freq = float(freqs[idx])
        amp_diff = float(diff[idx])
        lo = max(0, idx - 3)
        hi = min(power.shape[0], idx + 4)
        frame_db = 10 * np.log10(power[lo:hi, :].mean(axis=0) + 1e-15)
        frame_baseline = np.median(frame_db)
        persistence = float(np.mean(frame_db > frame_baseline + 2.0))

        confidence = round(min(0.95, 0.35 + 0.4 * min(amp_diff / 10, 1.0) + 0.25 * persistence), 2)

        findings.append({
            "frequency_hz": round(freq, 1),
            "amplitude_above_baseline_db": round(amp_diff, 2),
            "estimated_bandwidth_hz": round(float(freqs[min(hi, len(freqs) - 1)] - freqs[lo]), 1),
            "persistence": round(persistence, 2),
            "confidence": confidence,
        })

    findings.sort(key=lambda f: f["amplitude_above_baseline_db"], reverse=True)
    return findings[:max_results]
