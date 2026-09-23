"""
tempo_key.py — BPM and musical key estimation, with explicit confidence.
Never invents a value: below a confidence threshold, returns None and the
caller must display "Not confidently detected."
"""
from __future__ import annotations

import numpy as np
import librosa

BPM_CONFIDENCE_THRESHOLD = 0.35
KEY_CONFIDENCE_THRESHOLD = 0.4

KRUMHANSL_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KRUMHANSL_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def estimate_tempo(mono: np.ndarray, sample_rate: int) -> dict:
    if len(mono) < sample_rate * 4:
        return {"bpm": None, "confidence": 0.0, "note": "Track too short for tempo detection."}

    onset_env = librosa.onset.onset_strength(y=mono.astype(np.float32), sr=sample_rate)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sample_rate)
    tempo_val = float(np.atleast_1d(tempo)[0])

    # Confidence proxy: autocorrelation peak clarity of the onset envelope
    # around the detected tempo period.
    if len(onset_env) > 10 and tempo_val > 0:
        ac = librosa.autocorrelate(onset_env, max_size=len(onset_env))
        period_frames = int(round((60.0 / tempo_val) * sample_rate / 512))
        if 0 < period_frames < len(ac):
            peak = ac[period_frames]
            baseline = np.median(ac[1:]) + 1e-9
            confidence = float(min(1.0, max(0.0, (peak / baseline - 1) / 4)))
        else:
            confidence = 0.3
    else:
        confidence = 0.2

    if confidence < BPM_CONFIDENCE_THRESHOLD:
        return {"bpm": None, "confidence": round(confidence, 2), "note": "Not confidently detected."}

    return {"bpm": round(tempo_val, 1), "confidence": round(confidence, 2), "note": None}


def estimate_key(mono: np.ndarray, sample_rate: int) -> dict:
    if len(mono) < sample_rate * 4:
        return {"key": None, "confidence": 0.0, "note": "Track too short for key detection."}

    chroma = librosa.feature.chroma_cqt(y=mono.astype(np.float32), sr=sample_rate)
    chroma_mean = chroma.mean(axis=1)
    if np.sum(chroma_mean) <= 0:
        return {"key": None, "confidence": 0.0, "note": "Not confidently detected."}

    chroma_norm = chroma_mean / np.linalg.norm(chroma_mean)

    best_score, best_key = -np.inf, None
    scores = []
    for shift in range(12):
        major_profile = np.roll(KRUMHANSL_MAJOR, shift)
        minor_profile = np.roll(KRUMHANSL_MINOR, shift)
        major_score = float(np.dot(chroma_norm, major_profile / np.linalg.norm(major_profile)))
        minor_score = float(np.dot(chroma_norm, minor_profile / np.linalg.norm(minor_profile)))
        scores.append(major_score)
        scores.append(minor_score)
        if major_score > best_score:
            best_score, best_key = major_score, f"{PITCH_CLASSES[shift]} Major"
        if minor_score > best_score:
            best_score, best_key = minor_score, f"{PITCH_CLASSES[shift]} Minor"

    scores_sorted = sorted(scores, reverse=True)
    margin = scores_sorted[0] - scores_sorted[1] if len(scores_sorted) > 1 else 0
    confidence = float(min(1.0, max(0.0, margin * 6)))

    if confidence < KEY_CONFIDENCE_THRESHOLD:
        return {"key": None, "confidence": round(confidence, 2), "note": "Not confidently detected."}

    return {"key": best_key, "confidence": round(confidence, 2), "note": None}
