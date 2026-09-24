"""
jobs.py — simple in-process background job runner for V1.

Per spec: "If [Redis+Celery] introduces unnecessary complexity for local V1,
use a clean FastAPI background-job architecture." A single-machine local
tool doesn't need a message broker; a bounded ThreadPoolExecutor keeps
analysis off the request thread while remaining trivial to run locally.
The AnalysisJobRunner interface is intentionally narrow so it could be
swapped for a Celery/RQ-backed implementation later without touching the
API layer.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from . import storage
from audio_engine.pipeline import run_full_analysis, AnalysisError
from audio_engine.loader import AudioLoadError

logger = logging.getLogger("rawform.jobs")

_executor = ThreadPoolExecutor(max_workers=2)


def submit_analysis(analysis_id: str, file_path: str, original_filename: str,
                     genre: str, subprofile: str | None):
    _executor.submit(_run, analysis_id, file_path, original_filename, genre, subprofile)


def _run(analysis_id: str, file_path: str, original_filename: str,
          genre: str, subprofile: str | None):
    def progress(stage, pct):
        storage.update_progress(analysis_id, stage, pct)

    try:
        result = run_full_analysis(
            file_path, original_filename, genre=genre, subprofile=subprofile,
            progress_cb=progress,
        )
        result_path = storage.save_result_json(analysis_id, result)
        storage.mark_complete(
            analysis_id, result_path,
            result.get("mix_health", {}).get("overall_score"),
            result.get("metadata", {}).get("duration_seconds"),
        )
        except (AudioLoadError, AnalysisError) as exc:
        logger.exception("Analysis %s failed: %s", analysis_id, exc)
        storage.mark_failed(analysis_id, str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Analysis %s crashed unexpectedly", analysis_id)
        storage.mark_failed(analysis_id, "An unexpected error occurred during analysis.")
