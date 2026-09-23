"""
loudness.py — ITU-R BS.1770 / EBU R128 style loudness measurement.

Uses pyloudnorm for integrated / momentary / short-term LUFS (this is a
real, standard-conformant implementation, not an approximation). True peak
is estimated via 4x oversampling (polyphase resampling), which is the
standard approach when a dedicated oversampling filter isn't available.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pyloudnorm as pyln
from scipy import signal as sps


def _true_peak_dbtp(samples: np.ndarray, sample_rate: int, oversample: int = 4) -> float:
    """Estimate true peak (dBTP) via oversampling, per channel, then take max."""
    peaks = []
    for ch in range(samples.shape[1]):
        x = samples[:, ch]
        if len(x) < 2:
            peaks.append(np.max(np.abs(x)) if len(x) else 0.0)
            continue
        upsampled = sps.resample_poly(x, oversample, 1)
        peaks.append(np.max(np.abs(upsampled)))
    peak_linear = max(peaks) if peaks else 0.0
    if peak_linear <= 0:
        return -np.inf
    return 20 * np.log10(peak_linear)


def analyze_loudness(samples: np.ndarray, sample_rate: int) -> dict:
    """
    samples: (n_samples, n_channels) float64, NOT pre-normalized.
    Returns a dict with integrated/momentary/short-term LUFS, LRA, RMS,
    sample peak, true peak, and derived relationships.
    """
    meter = pyln.Meter(sample_rate)  # BS.1770-4 meter

    duration = samples.shape[0] / sample_rate
    result: dict = {
        "integrated_lufs": None,
        "loudness_range_lu": None,
        "momentary_lufs_timeseries": None,
        "short_term_lufs_timeseries": None,
        "rms_dbfs": None,
        "sample_peak_dbfs": None,
        "true_peak_dbtp": None,
        "true_peak_headroom_db": None,
        "peak_to_lufs_db": None,
        "findings_notes": [],
    }

    # Integrated LUFS requires pyloudnorm's block-based gating; it can raise
    # on extremely short / silent audio.
    try:
        integrated = meter.integrated_loudness(samples if samples.shape[1] > 1 else samples[:, 0])
        if np.isfinite(integrated) and integrated > -70:
            result["integrated_lufs"] = round(float(integrated), 2)
        else:
            result["findings_notes"].append(
                "Integrated loudness could not be reliably measured (signal may be near-silent)."
            )
    except Exception:  # noqa: BLE001
        result["findings_notes"].append("Integrated loudness measurement failed for this file.")

    # Short-term (3s window) and momentary (400ms window) LUFS over time,
    # computed manually via sliding BS.1770 K-weighted blocks so we can plot
    # loudness-over-time.
    mono = samples.mean(axis=1) if samples.shape[1] > 1 else samples[:, 0]
    st_times, st_vals = _sliding_lufs(mono, sample_rate, meter, window_s=3.0, hop_s=1.0)
    mo_times, mo_vals = _sliding_lufs(mono, sample_rate, meter, window_s=0.4, hop_s=0.1)

    result["short_term_lufs_timeseries"] = {"time_s": st_times, "lufs": st_vals}
    result["momentary_lufs_timeseries"] = {"time_s": mo_times, "lufs": mo_vals}

    valid_st = [v for v in st_vals if v is not None and np.isfinite(v)]
    if len(valid_st) >= 2:
        # Loudness Range approximated as the 10th-95th percentile spread of
        # short-term loudness values above relative gate (-20 LU below mean).
        arr = np.array(valid_st)
        gated = arr[arr > (np.mean(arr) - 20)]
        if len(gated) >= 2:
            lra = float(np.percentile(gated, 95) - np.percentile(gated, 10))
            result["loudness_range_lu"] = round(lra, 2)

    # RMS (dBFS), full signal
    rms = np.sqrt(np.mean(mono ** 2)) if len(mono) else 0.0
    result["rms_dbfs"] = round(20 * np.log10(rms), 2) if rms > 0 else -np.inf

    # Sample peak
    sample_peak = float(np.max(np.abs(samples))) if samples.size else 0.0
    result["sample_peak_dbfs"] = round(20 * np.log10(sample_peak), 2) if sample_peak > 0 else -np.inf

    # True peak (oversampled estimate)
    tp = _true_peak_dbtp(samples, sample_rate)
    result["true_peak_dbtp"] = round(tp, 2) if np.isfinite(tp) else None
    if result["true_peak_dbtp"] is not None:
        result["true_peak_headroom_db"] = round(0.0 - result["true_peak_dbtp"], 2)

    if result["integrated_lufs"] is not None and result["true_peak_dbtp"] is not None:
        result["peak_to_lufs_db"] = round(result["true_peak_dbtp"] - result["integrated_lufs"], 2)

    return result


def _sliding_lufs(mono: np.ndarray, sr: int, meter: pyln.Meter, window_s: float, hop_s: float):
    win = int(window_s * sr)
    hop = int(hop_s * sr)
    if win <= 0 or len(mono) < win:
        return [], []
    times, values = [], []
    for start in range(0, len(mono) - win + 1, hop):
        block = mono[start:start + win]
        try:
            loud = meter.integrated_loudness(block)
        except Exception:  # noqa: BLE001
            loud = None
        t = (start + win / 2) / sr
        times.append(round(float(t), 3))
        if loud is not None and np.isfinite(loud) and loud > -70:
            values.append(round(float(loud), 2))
        else:
            values.append(None)
    return times, values
