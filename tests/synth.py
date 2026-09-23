"""
synth.py — programmatically generate synthetic test signals used across
the DSP test suite, per the product spec's testing requirements.
"""
from __future__ import annotations

import numpy as np

SR = 44100


def sine_wave(freq=440.0, duration=2.0, sr=SR, amplitude=0.5, stereo=False):
    t = np.arange(int(duration * sr)) / sr
    mono = amplitude * np.sin(2 * np.pi * freq * t)
    if stereo:
        return np.stack([mono, mono], axis=1)
    return mono.reshape(-1, 1)


def stereo_sine(freq=440.0, duration=2.0, sr=SR, amplitude=0.5, phase_offset=0.0):
    t = np.arange(int(duration * sr)) / sr
    left = amplitude * np.sin(2 * np.pi * freq * t)
    right = amplitude * np.sin(2 * np.pi * freq * t + phase_offset)
    return np.stack([left, right], axis=1)


def kick_impulse(duration=0.3, sr=SR, freq=55.0, amplitude=0.9):
    """A simple synthetic kick: fast pitch/amplitude decay envelope."""
    t = np.arange(int(duration * sr)) / sr
    pitch_env = freq * (1 + 3 * np.exp(-t * 40))
    phase = 2 * np.pi * np.cumsum(pitch_env) / sr
    amp_env = amplitude * np.exp(-t * 18)
    click = 0.3 * amplitude * np.exp(-t * 400) * np.random.randn(len(t))
    sig = amp_env * np.sin(phase) + click
    return sig


def bass_tone(duration=0.5, sr=SR, freq=55.0, amplitude=0.6, sustain=True, fade_in_s=0.03):
    t = np.arange(int(duration * sr)) / sr
    env = np.ones_like(t) if sustain else np.exp(-t * 4)
    # soft fade-in so the bass note itself doesn't read as a percussive
    # onset/transient (keeps kick-onset detection clean in tests)
    fade_samples = min(len(t), int(fade_in_s * sr))
    if fade_samples > 1:
        env = env.copy()
        env[:fade_samples] *= np.linspace(0, 1, fade_samples)
    return amplitude * env * np.sin(2 * np.pi * freq * t)


def kick_bass_pattern(bpm=145, n_beats=16, sr=SR, kick_freq=55.0, bass_freq=55.0,
                       overlapping=True):
    """Kick -> Bass -> Kick -> Bass style pattern for kick_bass tests.

    Uses a CONTINUOUS sustained bass tone (so the bass itself never produces
    its own onset artifacts that could confuse kick detection) combined with
    regular kick transients.

    overlapping=True: bass plays at full level straight through each kick
    -> frequency + temporal competition in the post-kick window.
    overlapping=False: bass is briefly ducked (gated down) for ~120ms right
    after each kick, like a simple sidechain -> minimal competition in the
    post-kick window.
    """
    beat_dur = 60.0 / bpm
    total_samples = int(n_beats * beat_dur * sr)
    t_full = np.arange(total_samples) / sr

    # continuous bass tone, constant amplitude, no per-note onsets
    bass = 0.5 * np.sin(2 * np.pi * bass_freq * t_full)

    gate = np.ones(total_samples)
    duck_samples = int(0.13 * sr)
    ramp = int(0.02 * sr)
    for i in range(n_beats):
        start = int(i * beat_dur * sr)
        end = min(start + duck_samples, total_samples)
        if overlapping:
            # bass swells alongside the kick (clear temporal+frequency overlap)
            if end > start:
                gate[start:end] = 1.6
            r_end = min(end + ramp, total_samples)
            if r_end > end:
                gate[end:r_end] = np.linspace(1.6, 1.0, r_end - end)
        else:
            # simple sidechain-style duck away from the kick transient
            if end > start:
                gate[start:end] = 0.02
            r_end = min(end + ramp, total_samples)
            if r_end > end:
                gate[end:r_end] = np.linspace(0.02, 1.0, r_end - end)
    bass = bass * gate

    out = bass.copy()
    for i in range(n_beats):
        start = int(i * beat_dur * sr)
        k = kick_impulse(duration=min(0.25, beat_dur), sr=sr, freq=kick_freq, amplitude=0.9)
        end_k = min(start + len(k), total_samples)
        out[start:end_k] += k[: end_k - start]

    out = out / (np.max(np.abs(out)) + 1e-9) * 0.85
    return out.reshape(-1, 1)


def clipped_signal(duration=1.0, sr=SR, freq=200.0, drive=3.0):
    t = np.arange(int(duration * sr)) / sr
    sig = drive * np.sin(2 * np.pi * freq * t)
    sig = np.clip(sig, -1.0, 1.0)
    return sig.reshape(-1, 1)


def phase_inverted_stereo(freq=200.0, duration=1.0, sr=SR, amplitude=0.5):
    t = np.arange(int(duration * sr)) / sr
    left = amplitude * np.sin(2 * np.pi * freq * t)
    right = -left
    return np.stack([left, right], axis=1)


def broadband_noise(duration=1.0, sr=SR, amplitude=0.3, stereo=True, seed=42):
    rng = np.random.RandomState(seed)
    n = int(duration * sr)
    left = amplitude * rng.randn(n)
    if stereo:
        right = amplitude * rng.randn(n)
        return np.stack([left, right], axis=1)
    return left.reshape(-1, 1)


def silence(duration=1.0, sr=SR, stereo=True):
    n = int(duration * sr)
    if stereo:
        return np.zeros((n, 2))
    return np.zeros((n, 1))
