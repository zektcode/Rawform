"""
dynamics.py — crest factor, peak-to-RMS behavior, dynamic variation over time.
"""
from __future__ import annotations

import numpy as np


def analyze_dynamics(mono: np.ndarray, sample_rate: int) -> dict:
    result: dict = {
        "crest_factor_db": None,
        "peak_to_rms_db": None,
        "rms_over_time": None,
        "dynamic_variation_db": None,
        "notes": [],
    }

    if len(mono) == 0:
        result["notes"].append("No audio to analyze.")
        return result

    peak = np.max(np.abs(mono))
    rms_full = np.sqrt(np.mean(mono ** 2))
    if rms_full > 0 and peak > 0:
        crest = 20 * np.log10(peak / rms_full)
        result["crest_factor_db"] = round(float(crest), 2)
        result["peak_to_rms_db"] = round(float(crest), 2)

    # Short-window RMS over time (100ms windows, 50% overlap) for a
    # dynamics-over-time view and to measure variation.
    win = int(0.1 * sample_rate)
    hop = win // 2
    if win > 0 and len(mono) >= win:
        times, rms_vals = [], []
        for start in range(0, len(mono) - win + 1, hop):
            block = mono[start:start + win]
            r = np.sqrt(np.mean(block ** 2))
            db = 20 * np.log10(r) if r > 0 else -100.0
            times.append(round((start + win / 2) / sample_rate, 3))
            rms_vals.append(round(float(db), 2))
        result["rms_over_time"] = {"time_s": times, "rms_dbfs": rms_vals}

        finite_vals = [v for v in rms_vals if v > -99]
        if len(finite_vals) >= 2:
            variation = float(np.percentile(finite_vals, 95) - np.percentile(finite_vals, 5))
            result["dynamic_variation_db"] = round(variation, 2)

    # Interpretive notes (measurement-first, cautious language)
    cf = result["crest_factor_db"]
    if cf is not None:
        if cf < 6:
            result["notes"].append(
                "Low crest factor may indicate heavy compression or limiting, "
                "but this measurement alone does not prove it."
            )
        elif cf > 18:
            result["notes"].append(
                "High crest factor suggests significant unprocessed dynamic range, "
                "which is unusual for a fully mixed/mastered peak-time track but "
                "common for an early mix bounce."
            )

    return result
