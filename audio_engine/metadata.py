"""
metadata.py — basic file/audio metadata assembly.
"""
from __future__ import annotations

import os
from .loader import LoadedAudio
from . import tempo_key


def extract_metadata(loaded: LoadedAudio, original_filename: str) -> dict:
    bpm = tempo_key.estimate_tempo(loaded.mono, loaded.sample_rate)
    key = tempo_key.estimate_key(loaded.mono, loaded.sample_rate)

    return {
        "filename": original_filename,
        "duration_seconds": round(loaded.duration_seconds, 2),
        "sample_rate": loaded.sample_rate,
        "bit_depth": loaded.bit_depth,
        "channels": loaded.channels,
        "format": loaded.format,
        "subtype": loaded.subtype,
        "file_size_bytes": loaded.file_size_bytes,
        "bpm": bpm["bpm"],
        "bpm_confidence": bpm["confidence"],
        "bpm_note": bpm["note"],
        "key": key["key"],
        "key_confidence": key["confidence"],
        "key_note": key["note"],
    }
