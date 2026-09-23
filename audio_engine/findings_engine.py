"""
findings_engine.py — converts raw DSP measurements into evidence-backed
findings. Every finding has category/title/severity/confidence/evidence/
explanation/recommendations. Nothing is created "because it sounds
plausible" — each rule here is tied to a specific measured value.
"""
from __future__ import annotations

from typing import Any


def _sev(value: float, medium_th: float, high_th: float) -> str | None:
    if value >= high_th:
        return "high"
    if value >= medium_th:
        return "medium"
    return None


def build_findings(analysis: dict, genre_profile: dict) -> list[dict]:
    findings: list[dict] = []
    low_end = analysis.get("low_end", {})
    kick_bass = analysis.get("kick_bass", {})
    stereo = analysis.get("stereo", {})
    loudness = analysis.get("loudness", {})
    dynamics = analysis.get("dynamics", {})
    clipping = analysis.get("clipping", {})
    resonances = analysis.get("resonances", [])
    spectrum = analysis.get("spectrum", {})
    transients = analysis.get("transients", {})

    lp = genre_profile.get("low_end", {})
    sp = genre_profile.get("stereo", {})
    kp = genre_profile.get("kick_bass", {})

    # ---- LOW END --------------------------------------------------
    sub_rel = low_end.get("sub_energy_relative")
    if sub_rel is not None:
        th = lp.get("sub_overload_relative_threshold", 0.38)
        sev = _sev(sub_rel, th - 0.06, th)
        if sev:
            findings.append({
                "category": "low_end",
                "title": "Potential Sub Overload",
                "severity": sev,
                "confidence": 0.65,
                "frequency_range": [20, 40],
                "time_range": None,
                "evidence": [f"Approximately {sub_rel*100:.1f}% of low-end energy (20-300Hz) falls below 40 Hz."],
                "explanation": "A high proportion of energy concentrated below 40 Hz can reduce headroom and may translate poorly on smaller systems.",
                "recommendations": [
                    "Check the track on a full-range monitoring system and in mono.",
                    "Consider a high-pass filter or gentle shelf below ~30 Hz if this energy is not intentional.",
                    "Compare against a reference track in the same subgenre.",
                ],
            })

    low_mid_rel = low_end.get("low_mid_energy_relative")
    if low_mid_rel is not None:
        th = lp.get("low_mid_buildup_relative_threshold", 0.30)
        sev = _sev(low_mid_rel, th - 0.05, th)
        if sev:
            findings.append({
                "category": "low_end",
                "title": "Potential Low-Mid Buildup",
                "severity": sev,
                "confidence": 0.6,
                "frequency_range": [120, 300],
                "time_range": None,
                "evidence": [f"Approximately {low_mid_rel*100:.1f}% of low-end energy (20-300Hz) falls in the 120-300 Hz region."],
                "explanation": "Sustained buildup in 120-300 Hz is a common source of muddiness and can mask clarity in kick/bass and low percussion.",
                "recommendations": [
                    "Sweep a narrow EQ cut in this region and listen for whether clarity improves.",
                    "Check for multiple elements (bass, kick body, pads, low synths) overlapping here.",
                ],
            })

    if low_end.get("low_frequency_mono_compatible") is False:
        findings.append({
            "category": "low_end",
            "title": "Potential Low-End Phase Concern",
            "severity": "medium",
            "confidence": 0.55,
            "frequency_range": [20, 200],
            "time_range": None,
            "evidence": [f"Low-frequency stereo correlation measured at {low_end.get('low_frequency_stereo_correlation')}."],
            "explanation": "Low correlation in the 20-200 Hz range may indicate content that loses energy or partially cancels when summed to mono.",
            "recommendations": [
                "Audition the track in mono (use the Stereo/Mono toggle).",
                "Consider narrowing stereo width below ~150-200 Hz if mono compatibility matters for your release context (club systems, vinyl, radio).",
            ],
        })

    # ---- KICK / BASS ------------------------------------------------
    overlap_events = kick_bass.get("kick_bass_overlap_events", [])
    kick_count = kick_bass.get("kick_count", 0)
    overlap_ratio = (len(overlap_events) / kick_count) if kick_count else 0
    overlap_th = kp.get("overlap_ratio_flag_threshold", 0.30)
    if kick_count >= 4 and overlap_ratio >= overlap_th:
        conf = kick_bass.get("overall_overlap_confidence", 0.5)
        sev = "high" if overlap_ratio > 0.55 else "medium"
        times = [e["time_s"] for e in overlap_events[:5]]
        findings.append({
            "category": "kick_bass",
            "title": "Potential Kick/Bass Competition",
            "severity": sev,
            "confidence": conf,
            "frequency_range": [40, 120],
            "time_range": [times[0], times[-1]] if times else None,
            "evidence": [
                f"Strong simultaneous low-frequency energy detected during "
                f"{len(overlap_events)} of {kick_count} detected kick events "
                f"(examples near {', '.join(f'{t:.1f}s' for t in times)})."
            ],
            "explanation": "Kick and bass may be competing for the same spectral space and/or overlapping in time, which can reduce low-end clarity and punch.",
            "recommendations": [
                "Solo the kick and bass together and check for masking.",
                "Test a small EQ separation between kick fundamental and bass fundamental.",
                "Test sidechain/dynamic ducking of the bass on kick transients.",
                "Compare the result in mono.",
            ],
        })

    if kick_bass.get("kick_detection_confidence", 0) < 0.3 and kick_count > 0:
        findings.append({
            "category": "kick_bass",
            "title": "Low-Confidence Kick Detection",
            "severity": "low",
            "confidence": round(1 - kick_bass.get("kick_detection_confidence", 0), 2),
            "frequency_range": None,
            "time_range": None,
            "evidence": [f"Kick onset detection confidence: {kick_bass.get('kick_detection_confidence')}."],
            "explanation": "Kick transients in this track were not detected with high confidence, so kick/bass interaction findings above (if any) should be treated as exploratory.",
            "recommendations": ["Verify kick/bass balance by ear; consider isolating the kick channel if available for a more precise future stem-based analysis."],
        })

    # ---- STEREO -------------------------------------------------
    width_by_band = stereo.get("width_by_band") or []
    low_bands = [b for b in width_by_band if b["range_hz"][1] <= 200]
    if low_bands:
        avg_low_side = sum(b["side_ratio"] for b in low_bands) / len(low_bands)
        th = sp.get("low_end_width_flag_side_ratio", 0.35)
        if avg_low_side >= th:
            findings.append({
                "category": "stereo",
                "title": "Excessive Low-Frequency Stereo Width",
                "severity": "medium" if avg_low_side < th + 0.15 else "high",
                "confidence": 0.6,
                "frequency_range": [20, 200],
                "time_range": None,
                "evidence": [f"Average side-channel energy ratio below 200 Hz: {avg_low_side:.2f}."],
                "explanation": "Wide stereo content below 200 Hz can reduce mono compatibility and low-end translation on club and vinyl systems.",
                "recommendations": [
                    "Check mono compatibility using the Mono toggle.",
                    "Consider narrowing width below ~150-200 Hz if translation is a priority.",
                ],
            })

    if stereo.get("phase_correlation") is not None and stereo["phase_correlation"] < 0.15:
        findings.append({
            "category": "stereo",
            "title": "Potential Phase / Mono-Compatibility Issue",
            "severity": "high" if stereo["phase_correlation"] < 0 else "medium",
            "confidence": 0.55,
            "frequency_range": None,
            "time_range": None,
            "evidence": [f"Overall phase correlation measured at {stereo['phase_correlation']}."],
            "explanation": "Low or negative overall correlation can indicate phase issues that cause energy loss or cancellation in mono.",
            "recommendations": ["Audition in mono.", "Check any dual-mono or widened elements for phase relationships."],
        })

    # ---- LOUDNESS -------------------------------------------------
    tp = loudness.get("true_peak_dbtp")
    if tp is not None and tp > -0.3:
        findings.append({
            "category": "loudness",
            "title": "Low True-Peak Headroom",
            "severity": "high" if tp > 0 else "medium",
            "confidence": 0.85,
            "frequency_range": None,
            "time_range": None,
            "evidence": [f"Estimated true peak: {tp} dBTP."],
            "explanation": "Very low true-peak headroom increases the risk of intersample clipping/distortion during lossy encoding (e.g. streaming, club playback systems).",
            "recommendations": ["Leave additional true-peak headroom (commonly -1 dBTP or lower) before final export/mastering, especially if the track will be encoded to lossy formats."],
        })

    lra = loudness.get("loudness_range_lu")
    if lra is not None and lra > 12:
        findings.append({
            "category": "loudness",
            "title": "Large Loudness Variation",
            "severity": "medium",
            "confidence": 0.5,
            "frequency_range": None,
            "time_range": None,
            "evidence": [f"Estimated loudness range: {lra} LU."],
            "explanation": "Large loudness variation across the track may reflect intentional arrangement dynamics (breakdowns, builds) or inconsistent gain-staging between sections.",
            "recommendations": ["Review the loudness-over-time chart to confirm variation matches intended arrangement.", "Compare against a reference track's loudness curve."],
        })

    # ---- DYNAMICS ---------------------------------------------------
    cf = dynamics.get("crest_factor_db")
    if cf is not None and cf < 6:
        findings.append({
            "category": "dynamics",
            "title": "Very Flat Dynamics",
            "severity": "medium",
            "confidence": 0.5,
            "frequency_range": None,
            "time_range": None,
            "evidence": [f"Crest factor measured at {cf} dB."],
            "explanation": "Low crest factor may indicate heavy compression or limiting, but this measurement alone does not prove it — it may also be a deliberate peak-time production choice.",
            "recommendations": ["A/B against an earlier, less-processed bounce if available.", "Check for pumping or loss of transient impact on kick/percussion."],
        })

    # ---- CLIPPING -----------------------------------------------
    if clipping.get("clipping_detected"):
        findings.append({
            "category": "clipping",
            "title": "Digital Clipping Detected",
            "severity": "high",
            "confidence": 0.9,
            "frequency_range": None,
            "time_range": None,
            "evidence": [f"{clipping.get('clipped_sample_count')} samples at/above threshold across {len(clipping.get('clipping_events', []))} event(s)."],
            "explanation": "Digital clipping introduces audible distortion and is generally unintentional.",
            "recommendations": ["Check the export/bounce chain gain staging.", "Re-render from a version with adequate headroom if this was unintentional."],
        })

    # ---- RESONANCES -----------------------------------------------
    for r in resonances[:5]:
        if r["confidence"] < 0.4:
            continue
        findings.append({
            "category": "tonal",
            "title": f"Potential Resonance Around {r['frequency_hz']:.0f} Hz",
            "severity": "medium" if r["amplitude_above_baseline_db"] < 8 else "high",
            "confidence": r["confidence"],
            "frequency_range": [
                max(0, r["frequency_hz"] - r["estimated_bandwidth_hz"] / 2),
                r["frequency_hz"] + r["estimated_bandwidth_hz"] / 2,
            ],
            "time_range": None,
            "evidence": [f"Energy at {r['frequency_hz']:.0f} Hz exceeds the local spectral baseline by {r['amplitude_above_baseline_db']:.1f} dB, persistent in {r['persistence']*100:.0f}% of analyzed frames."],
            "explanation": "A narrow-band spectral peak like this can contribute to boxiness, harshness, or an unbalanced tonal character, depending on context.",
            "recommendations": [f"Sweep a narrow EQ cut around {r['frequency_hz']:.0f} Hz and listen for whether the resonance is actually contributing negatively.", "Check which element(s) are the source before applying a permanent cut."],
        })

    # ---- HARSHNESS (from spectrum + genre profile) -------------------
    centroid = spectrum.get("spectral_centroid_hz")
    bands = {b["range_hz"][0]: b for b in spectrum.get("bands", [])}
    harsh_energy = sum(
        bands[lo]["relative_energy"] for lo in [2000, 4000] if lo in bands
    ) if bands else None
    if harsh_energy is not None and harsh_energy > 0.22:
        findings.append({
            "category": "tonal",
            "title": "Potential Harshness in Upper-Mids",
            "severity": "medium",
            "confidence": 0.45,
            "frequency_range": [2000, 8000],
            "time_range": None,
            "evidence": [f"Relative energy in the 2-8kHz region: {harsh_energy*100:.1f}% of tracked spectral energy."],
            "explanation": "Elevated and persistent energy in the 2-8kHz range can read as harsh or fatiguing, especially at club playback volumes.",
            "recommendations": ["Reference against a track in the same subgenre.", "Check hats, percussion, and lead/FX layers for competing energy in this range."],
        })

    return findings
