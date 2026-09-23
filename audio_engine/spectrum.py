"""
spectrum.py — FFT/STFT spectral analysis: band energy, centroid, rolloff,
flatness, slope, flux, and averaged/log-scaled spectrum for display.
"""
from __future__ import annotations

import numpy as np
import librosa

# Standard band layout used across the app (Hz)
FREQUENCY_BANDS = [
    (20, 40), (40, 60), (60, 80), (80, 120), (120, 200),
    (200, 350), (350, 500), (500, 1000), (1000, 2000),
    (2000, 4000), (4000, 8000), (8000, 12000), (12000, 16000), (16000, 20000),
]


def _band_label(lo: int, hi: int) -> str:
    def fmt(v):
        return f"{v/1000:g}k" if v >= 1000 else str(v)
    return f"{fmt(lo)}-{fmt(hi)}Hz"


def compute_stft(mono: np.ndarray, sample_rate: int, n_fft: int = 4096, hop_length: int = 1024):
    S = librosa.stft(mono.astype(np.float32), n_fft=n_fft, hop_length=hop_length, window="hann")
    mag = np.abs(S)
    freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=n_fft)
    times = librosa.frames_to_time(np.arange(mag.shape[1]), sr=sample_rate, hop_length=hop_length)
    return mag, freqs, times


def analyze_spectrum(mono: np.ndarray, sample_rate: int) -> dict:
    result: dict = {
        "bands": [],
        "averaged_spectrum": None,
        "spectral_centroid_hz": None,
        "spectral_rolloff_hz": None,
        "spectral_flatness": None,
        "spectral_slope": None,
        "spectral_flux_mean": None,
        "spectrum_over_time": None,
        "notes": [],
    }

    if len(mono) < 2048:
        result["notes"].append("Track too short for full spectral analysis.")
        return result

    n_fft = 4096 if sample_rate >= 44100 else 2048
    hop_length = 1024
    mag, freqs, times = compute_stft(mono, sample_rate, n_fft=n_fft, hop_length=hop_length)
    power = mag ** 2
    avg_power = power.mean(axis=1)
    total_energy = float(avg_power.sum()) or 1e-12

    # Band energy (averaged over full track)
    for lo, hi in FREQUENCY_BANDS:
        if lo >= sample_rate / 2:
            continue
        mask = (freqs >= lo) & (freqs < hi)
        band_energy = float(avg_power[mask].sum())
        rel = band_energy / total_energy
        db = 10 * np.log10(band_energy + 1e-15)
        result["bands"].append({
            "range_hz": [lo, hi],
            "label": _band_label(lo, hi),
            "energy_db": round(db, 2),
            "relative_energy": round(rel, 5),
        })

    # Averaged spectrum (log-scaled frequency, for chart) — downsample to
    # ~300 log-spaced points so the frontend doesn't need to render 2048 bins.
    log_points = np.logspace(np.log10(max(20, freqs[1])), np.log10(sample_rate / 2), 300)
    avg_db = 10 * np.log10(avg_power + 1e-15)
    interp_db = np.interp(log_points, freqs, avg_db)
    result["averaged_spectrum"] = {
        "frequencies_hz": [round(float(f), 1) for f in log_points],
        "magnitude_db": [round(float(d), 2) for d in interp_db],
    }

    # Spectral descriptors (librosa)
    centroid = librosa.feature.spectral_centroid(S=mag, sr=sample_rate)[0]
    rolloff = librosa.feature.spectral_rolloff(S=mag, sr=sample_rate, roll_percent=0.85)[0]
    flatness = librosa.feature.spectral_flatness(S=mag)[0]
    if len(centroid):
        result["spectral_centroid_hz"] = round(float(np.mean(centroid)), 1)
    if len(rolloff):
        result["spectral_rolloff_hz"] = round(float(np.mean(rolloff)), 1)
    if len(flatness):
        result["spectral_flatness"] = round(float(np.mean(flatness)), 4)

    # Spectral slope: linear fit of log-magnitude vs log-frequency (dB/octave)
    valid = (freqs > 20) & (avg_db > -140)
    if valid.sum() > 10:
        log_f = np.log2(freqs[valid])
        slope, _ = np.polyfit(log_f, avg_db[valid], 1)
        result["spectral_slope"] = round(float(slope), 3)  # dB per octave

    # Spectral flux (frame-to-frame magnitude change, normalized)
    if mag.shape[1] > 1:
        diff = np.diff(mag, axis=1)
        flux = np.sqrt((diff ** 2).sum(axis=0))
        result["spectral_flux_mean"] = round(float(np.mean(flux)), 4)

    # Spectrum-over-time (coarse): band energy per ~1s frame, for a
    # spectrogram-lite timeline view without shipping the full STFT.
    frame_hop_s = 1.0
    frames_per_chunk = max(1, int(frame_hop_s * sample_rate / hop_length))
    n_chunks = max(1, mag.shape[1] // frames_per_chunk)
    band_edges = [b[0] for b in FREQUENCY_BANDS if b[0] < sample_rate / 2] + [
        min(FREQUENCY_BANDS[-1][1], int(sample_rate / 2))
    ]
    chunk_times, chunk_band_db = [], []
    for c in range(n_chunks):
        f0, f1 = c * frames_per_chunk, min((c + 1) * frames_per_chunk, mag.shape[1])
        if f0 >= f1:
            continue
        chunk_power = power[:, f0:f1].mean(axis=1)
        row = []
        for lo, hi in FREQUENCY_BANDS:
            if lo >= sample_rate / 2:
                continue
            mask = (freqs >= lo) & (freqs < hi)
            e = float(chunk_power[mask].sum())
            row.append(round(10 * np.log10(e + 1e-15), 2))
        chunk_times.append(round(float(times[f0]), 2))
        chunk_band_db.append(row)
    result["spectrum_over_time"] = {
        "time_s": chunk_times,
        "band_labels": [_band_label(lo, hi) for lo, hi in FREQUENCY_BANDS if lo < sample_rate / 2],
        "band_energy_db": chunk_band_db,
    }

    return result
