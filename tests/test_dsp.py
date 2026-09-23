import numpy as np
import pytest

from . import synth
from audio_engine import loudness, dynamics, spectrum, low_end, kick_bass, stereo, clipping, resonances, findings_engine, scoring


# ---------------------------------------------------------------- loudness
def test_loudness_sine_has_reasonable_lufs():
    sig = synth.sine_wave(freq=1000, duration=3.0, amplitude=0.5, stereo=True)
    result = loudness.analyze_loudness(sig, synth.SR)
    assert result["integrated_lufs"] is not None
    # A -6dBFS(ish) full-scale sine at 1kHz should read roughly -9 to -12 LUFS
    assert -20 < result["integrated_lufs"] < -3
    assert result["sample_peak_dbfs"] is not None
    assert result["true_peak_dbtp"] is not None


def test_loudness_louder_signal_has_higher_lufs():
    quiet = synth.sine_wave(freq=1000, duration=2.0, amplitude=0.1, stereo=True)
    loud = synth.sine_wave(freq=1000, duration=2.0, amplitude=0.8, stereo=True)
    r_quiet = loudness.analyze_loudness(quiet, synth.SR)
    r_loud = loudness.analyze_loudness(loud, synth.SR)
    assert r_loud["integrated_lufs"] > r_quiet["integrated_lufs"]


def test_true_peak_near_full_scale():
    sig = synth.sine_wave(freq=1000, duration=1.0, amplitude=0.999, stereo=True)
    result = loudness.analyze_loudness(sig, synth.SR)
    assert result["true_peak_dbtp"] > -1.0


# ---------------------------------------------------------------- dynamics / RMS / crest factor
def test_crest_factor_sine_is_moderate():
    sig = synth.sine_wave(freq=440, duration=2.0, amplitude=0.7, stereo=False)[:, 0]
    result = dynamics.analyze_dynamics(sig, synth.SR)
    # pure sine crest factor ~3dB theoretically
    assert result["crest_factor_db"] is not None
    assert 1.0 < result["crest_factor_db"] < 6.0


def test_clipped_signal_has_low_crest_factor():
    sig = synth.clipped_signal(duration=1.5)[:, 0]
    result = dynamics.analyze_dynamics(sig, synth.SR)
    assert result["crest_factor_db"] < 4.0


def test_rms_over_time_present():
    sig = synth.sine_wave(freq=300, duration=2.0, amplitude=0.5)[:, 0]
    result = dynamics.analyze_dynamics(sig, synth.SR)
    assert result["rms_over_time"] is not None
    assert len(result["rms_over_time"]["time_s"]) > 0


# ---------------------------------------------------------------- spectrum / bands
def test_spectrum_detects_dominant_frequency_band():
    sig = synth.sine_wave(freq=1500, duration=2.0, amplitude=0.5)[:, 0]
    result = spectrum.analyze_spectrum(sig, synth.SR)
    bands = {tuple(b["range_hz"]): b["relative_energy"] for b in result["bands"]}
    target_band = (1000, 2000)
    assert bands[target_band] == max(bands.values())


def test_spectral_centroid_near_tone_frequency():
    sig = synth.sine_wave(freq=2000, duration=2.0, amplitude=0.5)[:, 0]
    result = spectrum.analyze_spectrum(sig, synth.SR)
    assert abs(result["spectral_centroid_hz"] - 2000) < 300


def test_spectral_flatness_higher_for_noise_than_tone():
    tone = synth.sine_wave(freq=1000, duration=2.0, amplitude=0.5)[:, 0]
    noise = synth.broadband_noise(duration=2.0, stereo=False)[:, 0]
    r_tone = spectrum.analyze_spectrum(tone, synth.SR)
    r_noise = spectrum.analyze_spectrum(noise, synth.SR)
    assert r_noise["spectral_flatness"] > r_tone["spectral_flatness"]


# ---------------------------------------------------------------- stereo / phase
def test_phase_correlation_identical_channels_is_high():
    sig = synth.stereo_sine(freq=300, duration=2.0, phase_offset=0.0)
    result = stereo.analyze_stereo(sig[:, 0], sig[:, 1], synth.SR)
    assert result["phase_correlation"] > 0.9


def test_phase_correlation_inverted_channels_is_negative():
    sig = synth.phase_inverted_stereo(freq=300, duration=1.5)
    result = stereo.analyze_stereo(sig[:, 0], sig[:, 1], synth.SR)
    assert result["phase_correlation"] < -0.9
    assert result["mono_compatible"] is False


def test_mono_file_returns_not_applicable():
    result = stereo.analyze_stereo(None, None, synth.SR)
    assert result["is_stereo"] is False


# ---------------------------------------------------------------- clipping
def test_clipping_detected_on_clipped_signal():
    sig = synth.clipped_signal(duration=1.0)
    result = clipping.analyze_clipping(sig, synth.SR)
    assert result["clipping_detected"] is True
    assert result["clipped_sample_count"] > 0
    assert len(result["clipping_events"]) > 0


def test_clean_sine_not_flagged_as_clipped():
    sig = synth.sine_wave(freq=440, duration=1.0, amplitude=0.5, stereo=True)
    result = clipping.analyze_clipping(sig, synth.SR)
    assert result["clipping_detected"] is False


# ---------------------------------------------------------------- low end
def test_low_end_detects_sub_dominant_signal():
    sig = synth.sine_wave(freq=35, duration=2.0, amplitude=0.6)[:, 0]
    result = low_end.analyze_low_end(sig, synth.SR, None, None)
    assert result["sub_energy_relative"] > 0.7


def test_low_end_detects_bass_region():
    sig = synth.sine_wave(freq=90, duration=2.0, amplitude=0.6)[:, 0]
    result = low_end.analyze_low_end(sig, synth.SR, None, None)
    assert result["bass_energy_relative"] > 0.6


# ---------------------------------------------------------------- kick / bass
def test_kick_detection_on_synthetic_pattern():
    pattern = synth.kick_bass_pattern(bpm=145, n_beats=16, overlapping=True)[:, 0]
    result = kick_bass.analyze_kick_bass(pattern, synth.SR)
    # Should detect somewhere close to 16 kicks (allow tolerance for onset merging)
    assert result["kick_count"] >= 10
    assert result["kick_detection_confidence"] > 0


def test_kick_bass_overlap_flagged_when_overlapping():
    pattern = synth.kick_bass_pattern(bpm=145, n_beats=20, overlapping=True)[:, 0]
    result = kick_bass.analyze_kick_bass(pattern, synth.SR)
    assert len(result["kick_bass_overlap_events"]) > 0


def test_kick_bass_fewer_overlap_events_when_separated():
    overlapping = synth.kick_bass_pattern(bpm=145, n_beats=20, overlapping=True)[:, 0]
    separated = synth.kick_bass_pattern(bpm=145, n_beats=20, overlapping=False)[:, 0]
    r_overlap = kick_bass.analyze_kick_bass(overlapping, synth.SR)
    r_separated = kick_bass.analyze_kick_bass(separated, synth.SR)
    assert len(r_overlap["kick_bass_overlap_events"]) >= len(r_separated["kick_bass_overlap_events"])


# ---------------------------------------------------------------- resonances
def test_resonance_detected_for_narrow_peak_in_noise():
    rng = np.random.RandomState(1)
    n = int(3.0 * synth.SR)
    t = np.arange(n) / synth.SR
    noise = 0.05 * rng.randn(n)
    resonance_tone = 0.4 * np.sin(2 * np.pi * 800 * t)
    sig = noise + resonance_tone
    result = resonances.analyze_resonances(sig, synth.SR)
    assert len(result) > 0
    freqs = [r["frequency_hz"] for r in result]
    assert any(abs(f - 800) < 60 for f in freqs)


# ---------------------------------------------------------------- findings + scoring
def test_findings_engine_produces_clipping_finding():
    sig = synth.clipped_signal(duration=2.0, drive=4.0)
    stereo_sig = np.concatenate([sig, sig], axis=1)
    analysis = {
        "low_end": {}, "kick_bass": {}, "stereo": {},
        "loudness": {}, "dynamics": {},
        "clipping": clipping.analyze_clipping(stereo_sig, synth.SR),
        "resonances": [], "spectrum": {}, "transients": {},
    }
    profile = {"low_end": {}, "stereo": {}, "kick_bass": {}}
    findings = findings_engine.build_findings(analysis, profile)
    titles = [f["title"] for f in findings]
    assert "Digital Clipping Detected" in titles
    for f in findings:
        assert f["category"] and f["title"] and "confidence" in f


def test_scoring_no_findings_gives_perfect_scores():
    result = scoring.compute_mix_health([])
    assert result["overall_score"] == 100
    assert all(v == 100 for v in result["category_scores"].values())


def test_scoring_high_severity_finding_reduces_score():
    findings = [{
        "category": "clipping", "title": "Digital Clipping Detected",
        "severity": "high", "confidence": 0.9,
    }]
    result = scoring.compute_mix_health(findings)
    assert result["overall_score"] < 100
    assert result["category_scores"]["translation"] < 100
