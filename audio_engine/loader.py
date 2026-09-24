"""
loader.py — decoding, validation, preprocessing.

Responsibilities:
  * Decode WAV / AIFF / FLAC / MP3 into float64 numpy arrays.
  * Preserve original sample rate (no forced resampling).
  * Detect mono / stereo / multichannel.
  * Detect corrupt / unreadable files.
  * Provide a mono-sum representation for analyses that need it, while
    preserving the original stereo signal for stereo-specific analysis.
"""
from __future__ import annotations

import os
import struct
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import soundfile as sf

SUPPORTED_EXTENSIONS = {".wav", ".wave", ".aiff", ".aif", ".flac", ".mp3"}
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB, per spec
MIN_DURATION_SECONDS = 1.0


class AudioLoadError(Exception):
    """Raised when a file cannot be validated or decoded."""

    def __init__(self, message: str, code: str = "decode_error"):
        super().__init__(message)
        self.code = code


@dataclass
class LoadedAudio:
    # Original signal, shape (n_samples, n_channels), float64, NOT normalized.
    samples: np.ndarray
    sample_rate: int
    channels: int
    duration_seconds: float
    bit_depth: Optional[int]
    format: str
    subtype: Optional[str]
    original_path: str
    file_size_bytes: int

    # Derived, convenience representations -----------------------------
    mono: np.ndarray = field(init=False)  # mono sum (L+R)/2, float64
    left: Optional[np.ndarray] = field(init=False, default=None)
    right: Optional[np.ndarray] = field(init=False, default=None)

    def __post_init__(self):
        if self.channels >= 2:
            self.left = self.samples[:, 0]
            self.right = self.samples[:, 1]
            self.mono = (self.left + self.right) / 2.0
        else:
            self.mono = self.samples[:, 0] if self.samples.ndim == 2 else self.samples


def validate_file(path: str) -> None:
    if not os.path.exists(path):
        raise AudioLoadError("File does not exist.", "not_found")

    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise AudioLoadError(
            f"Unsupported file type '{ext}'. Supported: WAV, AIFF, FLAC, MP3.",
            "unsupported_type",
        )

    size = os.path.getsize(path)
    if size == 0:
        raise AudioLoadError("File is empty.", "empty_file")
    if size > MAX_FILE_SIZE_BYTES:
        raise AudioLoadError(
            f"File exceeds the {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB V1 limit.",
            "file_too_large",
        )


def _decode_with_ffmpeg(path: str) -> LoadedAudio:
    """Fallback decoder for formats soundfile can't read directly (e.g. some MP3s)."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", path,
                "-c:a", "pcm_f32le",
                tmp_path,
            ],
            capture_output=True,
            timeout=300,
        )
        if result.returncode != 0 or not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            raise AudioLoadError(
                "The file could not be decoded. It may be corrupt or in an unsupported variant of this format.",
                "corrupt_audio",
            )
        return _decode_with_soundfile(tmp_path, original_path=path, original_format="mp3")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _decode_with_soundfile(path: str, original_path: Optional[str] = None, original_format: Optional[str] = None) -> LoadedAudio:
    try:
        info = sf.info(path)
        data, sr = sf.read(path, always_2d=True, dtype="float32")
    except Exception as exc:  # noqa: BLE001
        raise AudioLoadError(
            "The file could not be decoded. It may be corrupt or use an unsupported codec.",
            "corrupt_audio",
        ) from exc

    if data.size == 0:
        raise AudioLoadError("Decoded audio contains no samples.", "corrupt_audio")

    duration = data.shape[0] / sr
    if duration < MIN_DURATION_SECONDS:
        raise AudioLoadError(
            f"Track is too short to analyze reliably ({duration:.2f}s). Minimum is {MIN_DURATION_SECONDS}s.",
            "too_short",
        )

    # bit depth from subtype where determinable
    bit_depth = None
    subtype = info.subtype
    if subtype:
        for token in ["64", "32", "24", "20", "16", "8"]:
            if token in subtype:
                bit_depth = int(token)
                break

    src_path = original_path or path
    fmt = original_format or (info.format or os.path.splitext(src_path)[1].lstrip(".")).lower()

    return LoadedAudio(
        samples=data,
        sample_rate=sr,
        channels=data.shape[1],
        duration_seconds=duration,
        bit_depth=bit_depth,
        format=fmt,
        subtype=subtype,
        original_path=src_path,
        file_size_bytes=os.path.getsize(src_path) if os.path.exists(src_path) else 0,
    )


def load_audio(path: str) -> LoadedAudio:
    """
    Decode an audio file into a LoadedAudio structure.
    Raises AudioLoadError on any validation/decoding failure — callers
    should catch this and surface a clean error, never a raw traceback.
    """
    validate_file(path)
    ext = os.path.splitext(path)[1].lower()

    if ext == ".mp3":
        # soundfile can't decode MP3 on most builds (no mpg123/lame backend) — use ffmpeg.
        try:
            return _decode_with_soundfile(path)
        except AudioLoadError:
            return _decode_with_ffmpeg(path)

    try:
        return _decode_with_soundfile(path)
    except AudioLoadError:
        # try ffmpeg as a last resort for unusual WAV/AIFF/FLAC variants
        return _decode_with_ffmpeg(path)
