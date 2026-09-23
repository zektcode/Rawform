"""
storage.py — filesystem + SQLite persistence layer.
Architected so PostgreSQL can swap in later (all SQL goes through this
module; no raw sqlite3 calls elsewhere).
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
ANALYSIS_DIR = os.path.join(BASE_DIR, "analysis")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DB_PATH = os.path.join(BASE_DIR, "backend", "rawform.db")

for d in (UPLOADS_DIR, ANALYSIS_DIR, REPORTS_DIR):
    os.makedirs(d, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    filename = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    return filename[-200:] or "upload"


def new_id() -> str:
    return uuid.uuid4().hex


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                genre TEXT NOT NULL,
                subprofile TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                progress_stage TEXT,
                progress_pct INTEGER DEFAULT 0,
                error_message TEXT,
                result_path TEXT,
                mix_health_score INTEGER,
                duration_seconds REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_reference INTEGER DEFAULT 0,
                reference_of TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                analysis_id TEXT NOT NULL,
                path TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_analysis_record(analysis_id: str, filename: str, stored_path: str,
                            genre: str, subprofile: str | None,
                            is_reference: bool = False, reference_of: str | None = None) -> None:
    with get_db() as conn:
        conn.execute(
            """INSERT INTO analyses
               (id, filename, stored_path, genre, subprofile, status, progress_pct,
                created_at, updated_at, is_reference, reference_of)
               VALUES (?, ?, ?, ?, ?, 'pending', 0, ?, ?, ?, ?)""",
            (analysis_id, filename, stored_path, genre, subprofile,
             now_iso(), now_iso(), int(is_reference), reference_of),
        )


def update_progress(analysis_id: str, stage: str, pct: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE analyses SET status='processing', progress_stage=?, progress_pct=?, updated_at=? WHERE id=?",
            (stage, pct, now_iso(), analysis_id),
        )


def mark_complete(analysis_id: str, result_path: str, mix_health_score, duration_seconds) -> None:
    with get_db() as conn:
        conn.execute(
            """UPDATE analyses SET status='complete', progress_pct=100, result_path=?,
               mix_health_score=?, duration_seconds=?, updated_at=? WHERE id=?""",
            (result_path, mix_health_score, duration_seconds, now_iso(), analysis_id),
        )


def mark_failed(analysis_id: str, error_message: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE analyses SET status='failed', error_message=?, updated_at=? WHERE id=?",
            (error_message, now_iso(), analysis_id),
        )


def get_analysis(analysis_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)).fetchone()
        return dict(row) if row else None


def list_analyses(limit: int = 100):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM analyses WHERE is_reference=0 ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def list_references(analysis_id: str):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM analyses WHERE reference_of=? ORDER BY created_at DESC",
            (analysis_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_analysis(analysis_id: str) -> bool:
    record = get_analysis(analysis_id)
    if not record:
        return False
    for path_key in ("stored_path", "result_path"):
        p = record.get(path_key)
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass
    with get_db() as conn:
        conn.execute("DELETE FROM analyses WHERE id=?", (analysis_id,))
    return True


def save_result_json(analysis_id: str, result: dict) -> str:
    path = os.path.join(ANALYSIS_DIR, f"{analysis_id}.json")
    with open(path, "w") as f:
        json.dump(result, f)
    return path


def load_result_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)
