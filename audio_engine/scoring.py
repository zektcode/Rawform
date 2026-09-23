"""
scoring.py — computes the Mix Health diagnostic score from findings, using
editable weights in config/scoring.json. This is a TECHNICAL diagnostic
score (how many measurement-backed findings were raised, weighted by
severity/confidence), not a musical-quality judgment.
"""
from __future__ import annotations

import json
import os

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "scoring.json")

# maps finding categories -> scoring categories
CATEGORY_MAP = {
    "low_end": "low_end",
    "kick_bass": "low_end",
    "tonal": "tonal",
    "dynamics": "dynamics",
    "stereo": "stereo",
    "loudness": "loudness",
    "clipping": "translation",
}
# stereo/low_end findings about mono-compatibility also affect "translation"
TRANSLATION_TRIGGER_TITLES = {
    "Potential Low-End Phase Concern",
    "Excessive Low-Frequency Stereo Width",
    "Potential Phase / Mono-Compatibility Issue",
    "Low True-Peak Headroom",
}


def load_scoring_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return json.load(f)


def compute_mix_health(findings: list[dict], config: dict | None = None) -> dict:
    config = config or load_scoring_config()
    weights = config["category_weights"]
    penalties = config["severity_penalty"]
    base = config["category_base_score"]
    floor = config["category_score_floor"]

    category_scores = {cat: base for cat in weights}

    for f in findings:
        target_cat = CATEGORY_MAP.get(f["category"])
        if target_cat and target_cat in category_scores:
            penalty = penalties.get(f["severity"], 5) * float(f.get("confidence", 0.5))
            category_scores[target_cat] -= penalty
        if f["title"] in TRANSLATION_TRIGGER_TITLES and "translation" in category_scores:
            penalty = penalties.get(f["severity"], 5) * float(f.get("confidence", 0.5)) * 0.6
            category_scores["translation"] -= penalty

    for cat in category_scores:
        category_scores[cat] = max(floor, min(100, round(category_scores[cat])))

    overall = sum(category_scores[c] * weights[c] for c in weights)
    overall = round(overall)

    return {
        "overall_score": overall,
        "category_scores": category_scores,
        "methodology_note": (
            "Technical diagnostic score based on measurement-backed findings, "
            "weighted by severity and confidence. Not a musical-quality judgment."
        ),
    }
