from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from backend import storage
from backend import jobs
from backend.report import generate_report_html
from audio_engine.loader import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_BYTES
from audio_engine.pipeline import load_genre_profile

app = FastAPI(title="Rawform Audio Engine API", version="0.1.0")

# ALLOWED_ORIGINS: comma-separated list of allowed origins, e.g.
#   ALLOWED_ORIGINS=https://rawform.vercel.app,https://rawform-git-main.vercel.app
# Defaults to "*" (any origin) for local/demo use — set this explicitly in
# production once you know your Vercel domain(s), for real CORS protection.
_allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "*").strip()
if _allowed_origins_env == "*":
    _allow_origins = ["*"]
    _allow_credentials = False  # wildcard + credentials is rejected by browsers anyway
else:
    _allow_origins = [o.strip() for o in _allowed_origins_env.split(",") if o.strip()]
    _allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage.init_db()

GENRES = ["techno", "psytrance"]


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/genres")
def get_genres():
    out = []
    for g in GENRES:
        profile = load_genre_profile(g)
        out.append({
            "id": profile["id"],
            "display_name": profile["display_name"],
            "default_subprofile": profile.get("default_subprofile"),
            "subprofiles": [
                {"id": k, "label": v.get("label", k)}
                for k, v in profile.get("subprofiles", {}).items()
            ],
        })
    return out


def _save_upload(file: UploadFile) -> tuple[str, str]:
    filename = storage.sanitize_filename(file.filename or "upload")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Supported: WAV, AIFF, FLAC, MP3.")

    analysis_id = storage.new_id()
    stored_name = f"{analysis_id}{ext}"
    stored_path = os.path.join(storage.UPLOADS_DIR, stored_name)

    size = 0
    with open(stored_path, "wb") as out:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_FILE_SIZE_BYTES:
                out.close()
                os.remove(stored_path)
                raise HTTPException(400, f"File exceeds the {MAX_FILE_SIZE_BYTES // (1024*1024)} MB V1 limit.")
            out.write(chunk)

    if size == 0:
        os.remove(stored_path)
        raise HTTPException(400, "Uploaded file is empty.")

    return analysis_id, stored_path


@app.post("/api/analyses")
def create_analysis(
    file: UploadFile = File(...),
    genre: str = Form("techno"),
    subprofile: str | None = Form(None),
):
    if genre not in GENRES:
        raise HTTPException(400, f"Unknown genre '{genre}'. Supported: {GENRES}")

    analysis_id, stored_path = _save_upload(file)
    original_filename = storage.sanitize_filename(file.filename or "upload")

    storage.create_analysis_record(analysis_id, original_filename, stored_path, genre, subprofile)
    jobs.submit_analysis(analysis_id, stored_path, original_filename, genre, subprofile)

    return {"id": analysis_id, "status": "pending"}


@app.get("/api/analyses")
def list_analyses():
    return storage.list_analyses()


@app.get("/api/analyses/{analysis_id}")
def get_analysis(analysis_id: str):
    record = storage.get_analysis(analysis_id)
    if not record:
        raise HTTPException(404, "Analysis not found.")

    response = {
        "id": record["id"],
        "filename": record["filename"],
        "genre": record["genre"],
        "subprofile": record["subprofile"],
        "status": record["status"],
        "progress_stage": record["progress_stage"],
        "progress_pct": record["progress_pct"],
        "error_message": record["error_message"],
        "mix_health_score": record["mix_health_score"],
        "duration_seconds": record["duration_seconds"],
        "created_at": record["created_at"],
    }

    if record["status"] == "complete" and record["result_path"]:
        try:
            response["result"] = storage.load_result_json(record["result_path"])
        except Exception:  # noqa: BLE001
            response["status"] = "failed"
            response["error_message"] = "Result data could not be loaded."

    return response


@app.delete("/api/analyses/{analysis_id}")
def delete_analysis(analysis_id: str):
    ok = storage.delete_analysis(analysis_id)
    if not ok:
        raise HTTPException(404, "Analysis not found.")
    return {"deleted": True}


@app.get("/api/analyses/{analysis_id}/audio")
def get_audio(analysis_id: str):
    record = storage.get_analysis(analysis_id)
    if not record or not os.path.exists(record["stored_path"]):
        raise HTTPException(404, "Audio file not found.")
    return FileResponse(record["stored_path"])


# ---------------------------------------------------------------- reference comparison

@app.post("/api/analyses/{analysis_id}/reference")
def create_reference(analysis_id: str, file: UploadFile = File(...)):
    record = storage.get_analysis(analysis_id)
    if not record:
        raise HTTPException(404, "Analysis not found.")

    ref_id, stored_path = _save_upload(file)
    original_filename = storage.sanitize_filename(file.filename or "reference")
    storage.create_analysis_record(
        ref_id, original_filename, stored_path, record["genre"], record["subprofile"],
        is_reference=True, reference_of=analysis_id,
    )
    jobs.submit_analysis(ref_id, stored_path, original_filename, record["genre"], record["subprofile"])
    return {"id": ref_id, "status": "pending"}


@app.get("/api/analyses/{analysis_id}/references")
def list_references(analysis_id: str):
    record = storage.get_analysis(analysis_id)
    if not record:
        raise HTTPException(404, "Analysis not found.")
    refs = storage.list_references(analysis_id)
    return [
        {
            "id": r["id"],
            "filename": r["filename"],
            "status": r["status"],
            "progress_pct": r["progress_pct"],
            "created_at": r["created_at"],
        }
        for r in refs
    ]


@app.get("/api/analyses/{analysis_id}/reference/{reference_id}/compare")
def compare_reference(analysis_id: str, reference_id: str):
    mine = storage.get_analysis(analysis_id)
    ref = storage.get_analysis(reference_id)
    if not mine or not ref:
        raise HTTPException(404, "Analysis or reference not found.")
    if mine["status"] != "complete" or ref["status"] != "complete":
        return {"status": "pending", "your_track_status": mine["status"], "reference_status": ref["status"]}

    my_result = storage.load_result_json(mine["result_path"])
    ref_result = storage.load_result_json(ref["result_path"])

    def diff(a, b):
        if a is None or b is None:
            return None
        return round(a - b, 2)

    comparison = {
        "your_track": {"filename": mine["filename"]},
        "reference": {"filename": ref["filename"]},
        "loudness": {
            "integrated_lufs": {
                "your_track": my_result["loudness"]["integrated_lufs"],
                "reference": ref_result["loudness"]["integrated_lufs"],
                "difference": diff(my_result["loudness"]["integrated_lufs"], ref_result["loudness"]["integrated_lufs"]),
            },
            "true_peak_dbtp": {
                "your_track": my_result["loudness"]["true_peak_dbtp"],
                "reference": ref_result["loudness"]["true_peak_dbtp"],
                "difference": diff(my_result["loudness"]["true_peak_dbtp"], ref_result["loudness"]["true_peak_dbtp"]),
            },
        },
        "dynamics": {
            "crest_factor_db": {
                "your_track": my_result["dynamics"]["crest_factor_db"],
                "reference": ref_result["dynamics"]["crest_factor_db"],
                "difference": diff(my_result["dynamics"]["crest_factor_db"], ref_result["dynamics"]["crest_factor_db"]),
            }
        },
        "stereo": {
            "phase_correlation": {
                "your_track": my_result["stereo"]["phase_correlation"],
                "reference": ref_result["stereo"]["phase_correlation"],
                "difference": diff(my_result["stereo"]["phase_correlation"], ref_result["stereo"]["phase_correlation"]),
            },
            "side_to_mid_ratio_db": {
                "your_track": my_result["stereo"]["side_to_mid_ratio_db"],
                "reference": ref_result["stereo"]["side_to_mid_ratio_db"],
                "difference": diff(my_result["stereo"]["side_to_mid_ratio_db"], ref_result["stereo"]["side_to_mid_ratio_db"]),
            },
        },
        "frequency_bands": [],
    }

    my_bands = {tuple(b["range_hz"]): b for b in my_result["spectrum"]["bands"]}
    ref_bands = {tuple(b["range_hz"]): b for b in ref_result["spectrum"]["bands"]}
    for key in my_bands:
        if key in ref_bands:
            comparison["frequency_bands"].append({
                "range_hz": list(key),
                "your_track_db": my_bands[key]["energy_db"],
                "reference_db": ref_bands[key]["energy_db"],
                "difference_db": diff(my_bands[key]["energy_db"], ref_bands[key]["energy_db"]),
            })

    return {"status": "complete", "comparison": comparison}


# ---------------------------------------------------------------- report

@app.get("/api/analyses/{analysis_id}/report")
def get_report(analysis_id: str):
    record = storage.get_analysis(analysis_id)
    if not record:
        raise HTTPException(404, "Analysis not found.")
    if record["status"] != "complete" or not record["result_path"]:
        raise HTTPException(400, "Analysis is not complete yet.")

    result = storage.load_result_json(record["result_path"])
    html_report = generate_report_html(result)

    report_id = storage.new_id()
    report_path = os.path.join(storage.REPORTS_DIR, f"{report_id}.html")
    with open(report_path, "w") as f:
        f.write(html_report)

    return FileResponse(report_path, media_type="text/html", filename=f"rawform_report_{record['filename']}.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
