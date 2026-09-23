"""
clipping.py — digital clipping / consecutive-full-scale-sample detection,
plus a coarse intersample-peak concern flag using the oversampled true peak.
"""
from __future__ import annotations

import numpy as np


def analyze_clipping(samples: np.ndarray, sample_rate: int, threshold: float = 0.999) -> dict:
    result = {
        "clipped_sample_count": 0,
        "clipping_events": [],
        "clipping_detected": False,
        "peak_linear": None,
        "intersample_peak_concern": False,
        "notes": [],
    }
    if samples.size == 0:
        return result

    peak = float(np.max(np.abs(samples)))
    result["peak_linear"] = round(peak, 5)

    abs_max = np.max(np.abs(samples), axis=1) if samples.ndim == 2 else np.abs(samples)
    clipped_mask = abs_max >= threshold
    count = int(np.sum(clipped_mask))
    result["clipped_sample_count"] = count
    result["clipping_detected"] = count > 0

    if count > 0:
        # group consecutive clipped samples into events with timestamps
        idx = np.where(clipped_mask)[0]
        gaps = np.where(np.diff(idx) > int(0.01 * sample_rate))[0]
        starts = np.concatenate(([0], gaps + 1))
        ends = np.concatenate((gaps, [len(idx) - 1]))
        events = []
        for s, e in zip(starts, ends):
            start_sample, end_sample = idx[s], idx[e]
            events.append({
                "start_time_s": round(start_sample / sample_rate, 3),
                "end_time_s": round(end_sample / sample_rate, 3),
                "sample_count": int(end_sample - start_sample + 1),
            })
            if len(events) >= 200:
                break
        result["clipping_events"] = events
        result["notes"].append(
            f"{count} samples at or above {threshold:.3f} full scale detected across "
            f"{len(events)} event(s). Check the source bounce/export settings."
        )

    if peak >= 0.999:
        result["intersample_peak_concern"] = True
        result["notes"].append(
            "Sample peak is at or near 0 dBFS. True-peak (oversampled) measurement "
            "in the Loudness tab should be checked for intersample overs."
        )

    return result
