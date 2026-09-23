# Rawform backend — real Python DSP engine (librosa/numpy/scipy/pyloudnorm)
# behind FastAPI. This is NOT meant for Vercel serverless functions: the
# native audio libraries are too large for Vercel's function size limit and
# analysis can legitimately take longer than Vercel's execution time limits.
# Deploy this image to a real-container host instead: Railway, Render, or
# Fly.io all auto-detect this Dockerfile. See DEPLOY.md.

FROM python:3.12-slim

# ffmpeg is used as a decode fallback (and for MP3 input) by audio_engine/loader.py
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first so Docker layer caching keeps rebuilds fast
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# App code
COPY audio_engine/ audio_engine/
COPY backend/ backend/
COPY config/ config/

RUN mkdir -p uploads analysis reports

# Railway/Render/Fly all inject $PORT at runtime; shell-form CMD lets it
# expand at container start rather than at build time. Default to 8000 for
# hosts that don't set it (e.g. plain `docker run`).
ENV PORT=8000
EXPOSE 8000
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
