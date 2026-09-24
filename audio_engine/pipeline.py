"""
pipeline.py — orchestrates the full analysis pipeline: load -> preprocess ->
run all DSP modules -> findings -> scoring -> structured result dict.

This is the single entry point other consumers (FastAPI backend today;
VST3/desktop/CLI in the future) should call.
"""
from __future__ import annotations

import json
import os
import time
import traceback

from . import metadata as metadata_mod
from . import loudness as loudness_mod
from . import dynamics as dynamics_mod
from . import spectrum as spectrum_mod
from . import low_end as low_end_mod
from . import kick_bass as kick_bass_mod
from . import stereo as stereo_mod
from . import clipping as clipping_mod
from . import transients as transients_mod
from . import resonances as resonances_mod
from . import findings_engine
from . import scoring
from .loader import load_audio, AudioLoadError

_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config", "profiles")

_GENRE_CACHE: dict[str, dict] = {}


def load_genre_profile(genre: str) -> dict:
    if genre in _GENRE_CACHE:
        return _GENRE_CACHE[genre]
    path = os.path.join(_CONFIG_DIR, f"{genre}.json")
    if not os.path.exists(path):
        raise ValueError(f"Unknown genre profile: {genre}")
    with open(path) as f:
        profile = json.load(f)
    _GENRE_CACHE[genre] = profile
    return profile


class AnalysisError(Exception):
    def __init__(self, message: str, code: str = "analysis_failed"):
        super().__init__(message)
        self.code = code


def run_full_analysis(
    file_path: str,
    original_filename: str,
    genre: str = "techno",
    subprofile: str | None = None,
    progress_cb=None,
) -> dict:
    """
    Runs the complete analysis pipeline on a local audio file.
    progress_cb(stage: str, pct: int) is optional, called as stages complete.
    Raises AudioLoadError / AnalysisError on failure — callers must not leak
    raw tracebacks to end users.
    """
    def report(stage, pct):
        if progress_cb:
            try:
                progress_cb(stage, pct)
            except Exception:  # noqa: BLE001
                pass

    start = time.time()
    report("loading", 5)
    loaded = load_audio(file_path)  # raises AudioLoadError on failure

    genre_profile = load_genre_profile(genre)
    sub = subprofile or genre_profile.get("default_subprofile")
    subprofile_config = genre_profile.get("subprofiles", {}).get(sub, {})

    try:
        report("metadata", 10)
        meta = metadata_mod.extract_metadata(loaded, original_filename)

        report("loudness", 20)
        loud = loudness_mod.analyze_loudness(loaded.samples, loaded.sample_rate)

        report("dynamics", 30)
        dyn = dynamics_mod.analyze_dynamics(loaded.mono, loaded.sample_rate)

        report("spectrum", 45)
        spec = spectrum_mod.analyze_spectrum(loaded.mono, loaded.sample_rate)

        report("low_end", 55)
        low = low_end_mod.analyze_low_end(loaded.mono, loaded.sample_rate, loaded.left, loaded.right)

        report("kick_bass", 65)
        kb = kick_bass_mod.analyze_kick_bass(loaded.mono, loaded.sample_rate)

        report("stereo", 75)
        st = stereo_mod.analyze_stereo(loaded.left, loaded.right, loaded.sample_rate)

        report("clipping", 80)
        clip = clipping_mod.analyze_clipping(loaded.samples, loaded.sample_rate)

        report("transients", 85)
        trans = transients_mod.analyze_transients(loaded.mono, loaded.sample_rate)

        report("resonances", 90)
        reson = resonances_mod.analyze_resonances(loaded.mono, loaded.sample_rate)

    except Exception as exc:  # noqa: BLE001
        raise AnalysisError(
            f"DEBUG: {type(exc).__name__}: {exc}",
        ) from exc

    analysis = {
        "metadata": meta,
        "loudness": loud,
        "dynamics": dyn,
        "spectrum": spec,
        "low_end": low,
        "kick_bass": kb,
        "stereo": st,
        "clipping": clip,
        "transients": trans,
        "resonances": reson,
    }

    report("findings", 95)
    try:
        findings = findings_engine.build_findings(analysis, genre_profile)
        health = scoring.compute_mix_health(findings)
    except Exception:  # noqa: BLE001
        findings = []
        health = {"overall_score": None, "category_scores": {}, "methodology_note": "Scoring failed."}

    analysis["findings"] = findings
    analysis["mix_health"] = health
    analysis["genre"] = {
        "id": genre_profile["id"],
        "display_name": genre_profile["display_name"],
        "subprofile": sub,
        "subprofile_label": subprofile_config.get("label", sub),
    }
    analysis["recommendations"] = _aggregate_recommendations(findings)
    analysis["processing_time_seconds"] = round(time.time() - start, 2)
    analysis["engine_version"] = "0.1.0"
    analysis["disclaimers"] = [
        "This is a technical diagnostic tool, not an objective judge of musical quality.",
        "Findings are heuristic and confidence-scored; they are not guaranteed conclusions.",
        "The producer remains the final decision-maker.",
    ]

    return analysis


def _aggregate_recommendations(findings: list[dict]) -> list[str]:
    seen = []
    for f in findings:
        for r in f.get("recommendations", []):
            if r not in seen:
                seen.append(r)
    return seen[:12]
