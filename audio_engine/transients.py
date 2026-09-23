"""
transients.py — broadband transient detection, density, and strength.
"""
from __future__ import annotations

import numpy as np
import librosa


def analyze_transients(mono: np.ndarray, sample_rate: int) -> dict:
    result = {
        "transient_count": 0,
        "transient_times_s": [],
        "transient_density_per_10s": None,
        "mean_transient_strength": None,
        "notes": [],
    }
    if len(mono) < sample_rate:
        result["notes"].append("Track too short for transient analysis.")
        return result

    hop_length = 512
    onset_env = librosa.onset.onset_strength(y=mono.astype(np.float32), sr=sample_rate, hop_length=hop_length)
    if len(onset_env) < 4 or np.max(onset_env) <= 0:
        return result

    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sample_rate, hop_length=hop_length,
        backtrack=False, delta=0.1, wait=4,
    )
    times = librosa.frames_to_time(onset_frames, sr=sample_rate, hop_length=hop_length)
    strengths = onset_env[onset_frames] if len(onset_frames) else np.array([])

    result["transient_count"] = len(times)
    result["transient_times_s"] = [round(float(t), 3) for t in times][:2000]
    duration = len(mono) / sample_rate
    if duration > 0:
        result["transient_density_per_10s"] = round(len(times) / duration * 10, 2)
    if len(strengths):
        result["mean_transient_strength"] = round(float(np.mean(strengths)), 3)

    if result["transient_density_per_10s"] and result["transient_density_per_10s"] > 60:
        result["notes"].append(
            "Very high transient density detected — may indicate a dense percussion "
            "arrangement or busy sound design; not inherently a problem."
        )

    return result
