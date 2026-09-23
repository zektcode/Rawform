"""
low_end.py — sub/bass/low-mid energy, stereo width of the low end, and
mono-compatibility of the low end. This feeds genre-specific interpretation
in the findings engine (techno.json / psytrance.json thresholds).
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfiltfilt

LOW_END_BANDS = [
    (20, 40), (40, 60), (60, 80), (80, 120), (120, 200), (200, 300),
]


def _bandpass(x: np.ndarray, sr: int, lo: float, hi: float) -> np.ndarray:
    nyq = sr / 2
    lo_n = max(lo / nyq, 1e-5)
    hi_n = min(hi / nyq, 0.999)
    if lo_n >= hi_n:
        return np.zeros_like(x)
    sos = butter(4, [lo_n, hi_n], btype="band", output="sos")
    return sosfiltfilt(sos, x)


def analyze_low_end(mono: np.ndarray, sample_rate: int,
                     left: np.ndarray | None, right: np.ndarray | None) -> dict:
    result: dict = {
        "bands": [],
        "sub_energy_relative": None,
        "bass_energy_relative": None,
        "low_mid_energy_relative": None,
        "low_frequency_stereo_correlation": None,
        "low_frequency_mono_compatible": None,
        "energy_consistency": None,
        "dominant_region_hz": None,
        "notes": [],
    }

    if len(mono) < sample_rate * 0.5:
        result["notes"].append("Track too short for low-end analysis.")
        return result

    band_energies = []
    for lo, hi in LOW_END_BANDS:
        if lo >= sample_rate / 2:
            continue
        filtered = _bandpass(mono, sample_rate, lo, hi)
        energy = float(np.mean(filtered ** 2))
        band_energies.append((lo, hi, energy))

    total = sum(e for _, _, e in band_energies) or 1e-12
    for lo, hi, e in band_energies:
        rel = e / total
        result["bands"].append({
            "range_hz": [lo, hi],
            "relative_energy": round(rel, 4),
            "energy_db": round(10 * np.log10(e + 1e-15), 2),
        })

    # sub (20-40), bass (40-120), low-mid (120-300) rollups
    def sum_range(lo_bound, hi_bound):
        return sum(e for lo, hi, e in band_energies if lo >= lo_bound and hi <= hi_bound)

    sub = sum_range(20, 40)
    bass = sum_range(40, 120)
    low_mid = sum_range(120, 300)
    result["sub_energy_relative"] = round(sub / total, 4)
    result["bass_energy_relative"] = round(bass / total, 4)
    result["low_mid_energy_relative"] = round(low_mid / total, 4)

    if band_energies:
        dominant = max(band_energies, key=lambda b: b[2])
        result["dominant_region_hz"] = [dominant[0], dominant[1]]

    # Consistency: how stable is low-end (20-200Hz) energy over 1s windows —
    # low variation = consistent (typical of a steady sub/bass part), high
    # variation may indicate inconsistent bass takes or arrangement changes.
    filtered_full = _bandpass(mono, sample_rate, 20, 200)
    win = int(1.0 * sample_rate)
    if len(filtered_full) >= win * 2:
        chunk_rms = []
        for start in range(0, len(filtered_full) - win, win):
            block = filtered_full[start:start + win]
            chunk_rms.append(np.sqrt(np.mean(block ** 2)))
        chunk_rms = np.array([c for c in chunk_rms if c > 1e-9])
        if len(chunk_rms) >= 2:
            cv = float(np.std(chunk_rms) / np.mean(chunk_rms))
            result["energy_consistency"] = round(max(0.0, 1.0 - min(cv, 1.0)), 3)

    # Stereo correlation / mono compatibility of the low end specifically
    if left is not None and right is not None:
        l_low = _bandpass(left, sample_rate, 20, 200)
        r_low = _bandpass(right, sample_rate, 20, 200)
        n = min(len(l_low), len(r_low))
        if n > sample_rate:
            l_low, r_low = l_low[:n], r_low[:n]
            denom = np.sqrt(np.sum(l_low ** 2) * np.sum(r_low ** 2))
            corr = float(np.sum(l_low * r_low) / denom) if denom > 0 else None
            result["low_frequency_stereo_correlation"] = round(corr, 3) if corr is not None else None
            if corr is not None:
                result["low_frequency_mono_compatible"] = bool(corr > 0.5)

    # Interpretive notes
    if result["sub_energy_relative"] and result["sub_energy_relative"] > 0.35:
        result["notes"].append(
            "Unusually high proportion of low-end energy is concentrated below 40 Hz. "
            "Worth checking on a full-range system and in mono."
        )
    if result["low_mid_energy_relative"] and result["low_mid_energy_relative"] > 0.30:
        result["notes"].append(
            "Sustained energy around 120-300 Hz is comparatively high relative to sub/bass — "
            "possible low-mid buildup worth investigating."
        )
    if result["low_frequency_mono_compatible"] is False:
        result["notes"].append(
            "Low-frequency stereo correlation is low. On systems that sum to mono, "
            "sub/bass content in this range may lose energy or cancel."
        )

    return result
