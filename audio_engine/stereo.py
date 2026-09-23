"""
stereo.py — stereo field, phase correlation, Mid/Side balance, mono
compatibility (full mix + per band).
"""
from __future__ import annotations

import numpy as np
from .spectrum import FREQUENCY_BANDS, compute_stft


def analyze_stereo(left: np.ndarray | None, right: np.ndarray | None, sample_rate: int) -> dict:
    result: dict = {
        "is_stereo": left is not None and right is not None,
        "left_rms_dbfs": None,
        "right_rms_dbfs": None,
        "lr_balance_db": None,
        "phase_correlation": None,
        "mono_compatible": None,
        "mid_energy_relative": None,
        "side_energy_relative": None,
        "side_to_mid_ratio_db": None,
        "correlation_over_time": None,
        "width_by_band": None,
        "notes": [],
    }

    if left is None or right is None:
        result["notes"].append("File is mono — stereo-specific analysis not applicable.")
        return result

    n = min(len(left), len(right))
    left, right = left[:n], right[:n]

    def rms_db(x):
        r = np.sqrt(np.mean(x ** 2))
        return round(20 * np.log10(r), 2) if r > 0 else -np.inf

    result["left_rms_dbfs"] = rms_db(left)
    result["right_rms_dbfs"] = rms_db(right)
    if np.isfinite(result["left_rms_dbfs"]) and np.isfinite(result["right_rms_dbfs"]):
        result["lr_balance_db"] = round(result["left_rms_dbfs"] - result["right_rms_dbfs"], 2)

    # Overall phase correlation
    denom = np.sqrt(np.sum(left ** 2) * np.sum(right ** 2))
    corr = float(np.sum(left * right) / denom) if denom > 0 else None
    result["phase_correlation"] = round(corr, 3) if corr is not None else None
    if corr is not None:
        result["mono_compatible"] = bool(corr > 0.3)

    # Mid/Side
    mid = (left + right) / 2.0
    side = (left - right) / 2.0
    mid_e = float(np.mean(mid ** 2))
    side_e = float(np.mean(side ** 2))
    total = mid_e + side_e + 1e-15
    result["mid_energy_relative"] = round(mid_e / total, 4)
    result["side_energy_relative"] = round(side_e / total, 4)
    if mid_e > 0 and side_e > 0:
        result["side_to_mid_ratio_db"] = round(10 * np.log10(side_e / mid_e), 2)

    # Correlation over time (1s windows) — helps show width changes across sections
    win = int(1.0 * sample_rate)
    if n >= win * 2:
        times, corr_vals = [], []
        for start in range(0, n - win, win):
            lb, rb = left[start:start + win], right[start:start + win]
            d = np.sqrt(np.sum(lb ** 2) * np.sum(rb ** 2))
            c = float(np.sum(lb * rb) / d) if d > 0 else 0.0
            times.append(round(start / sample_rate, 2))
            corr_vals.append(round(c, 3))
        result["correlation_over_time"] = {"time_s": times, "correlation": corr_vals}

    # Width by frequency band — side/mid energy ratio per band
    mag_l, freqs, _ = compute_stft(left, sample_rate, n_fft=4096, hop_length=2048)
    mag_r, _, _ = compute_stft(right, sample_rate, n_fft=4096, hop_length=2048)
    mid_spec = (mag_l + mag_r) / 2.0
    side_spec = np.abs(mag_l - mag_r) / 2.0
    band_widths = []
    for lo, hi in FREQUENCY_BANDS:
        if lo >= sample_rate / 2:
            continue
        mask = (freqs >= lo) & (freqs < hi)
        m = float((mid_spec[mask] ** 2).sum())
        s = float((side_spec[mask] ** 2).sum())
        ratio = s / (m + s + 1e-15)
        band_widths.append({"range_hz": [lo, hi], "side_ratio": round(ratio, 3)})
    result["width_by_band"] = band_widths

    # Notes
    if result["phase_correlation"] is not None and result["phase_correlation"] < 0.2:
        result["notes"].append(
            "Overall phase correlation is low. Worth checking mono compatibility — "
            "some content may lose energy when summed to mono."
        )
    low_bands = [b for b in band_widths if b["range_hz"][1] <= 200]
    if low_bands and np.mean([b["side_ratio"] for b in low_bands]) > 0.35:
        result["notes"].append(
            "Notable stereo width detected below 200 Hz. Wide low end can reduce "
            "mono compatibility and translation on club systems — worth checking."
        )

    return result
