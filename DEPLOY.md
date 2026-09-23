# Deploying Rawform to the web

## Why two hosts, not just Vercel

Vercel is excellent for the Next.js frontend — that part deploys with zero
config. But the backend is a real Python audio-DSP engine (librosa, numpy,
scipy, numba under the hood, pyloudnorm) doing real signal processing on
uploaded files. That doesn't fit Vercel's **serverless functions**:

- **Size**: librosa's dependency tree (numba/llvmlite + scipy + numpy)
  is too large for Vercel's serverless function size limit.
- **Time**: analysis of a real track can take longer than Vercel's function
  execution limits (10s on Hobby, 60s on Pro without special config), and
  numba JIT-compiles some of librosa's hot paths on first call, which adds
  cold-start latency on top of that.
- **State**: a serverless function is stateless per-invocation; our
  background-job + SQLite-status-polling design assumes a long-lived
  process, which serverless functions aren't.

So: **frontend on Vercel, backend on a real-container host** (Railway,
Render, or Fly.io — pick one; instructions below use Railway since it's the
fastest to set up). They talk to each other over HTTPS.

```
 Phone/Browser
      │
      ▼
 Vercel (Next.js frontend)  ──HTTPS──▶  Railway (FastAPI + DSP engine, Docker)
```

---

## 1. Push this to GitHub

Vercel and Railway both deploy from a GitHub repo.

```bash
cd rawform
git init
git add .
git commit -m "Rawform V1"
```
Create a new repo on GitHub (github.com/new), then:
```bash
git remote add origin https://github.com/<you>/rawform.git
git branch -M main
git push -u origin main
```

## 2. Deploy the backend to Railway

1. Go to **railway.app** → sign in with GitHub.
2. **New Project → Deploy from GitHub repo** → select your `rawform` repo.
3. Railway auto-detects the `Dockerfile` at the repo root and builds it —
   no configuration needed. (The Dockerfile only copies `backend/`,
   `audio_engine/`, and `config/` into the image; the frontend is ignored
   via `.dockerignore`.)
4. Once it's deployed, go to the service's **Settings → Networking →
   Generate Domain**. You'll get a URL like:
   `https://rawform-production-xxxx.up.railway.app`
5. Verify it's alive: open `<that-url>/api/health` in a browser — should
   show `{"status":"ok"}`. First load may take 10-20s (cold start +
   importing the audio libraries).

Keep that URL — you need it in the next step.

## 3. Deploy the frontend to Vercel

1. Go to **vercel.com** → sign in with GitHub.
2. **Add New → Project** → import the same `rawform` repo.
3. In the import screen, expand and set:
   - **Root Directory**: `frontend`
   - Framework preset: Next.js (auto-detected)
4. Add an **Environment Variable** before deploying:
   - `NEXT_PUBLIC_API_BASE` = the Railway URL from step 2
     (e.g. `https://rawform-production-xxxx.up.railway.app`)
   - Apply to Production (and Preview if you want preview deploys to also work)
5. Click **Deploy**.

You'll get a URL like `https://rawform.vercel.app` — that's your live app,
reachable from any phone/browser, no LAN required.

## 4. Lock down CORS (recommended, takes 1 minute)

Right now the backend accepts requests from any origin (`ALLOWED_ORIGINS`
defaults to `*`). Once you know your Vercel domain, restrict it:

1. Railway → your backend service → **Variables**
2. Add: `ALLOWED_ORIGINS` = `https://rawform.vercel.app` (your actual
   domain; comma-separate multiple, e.g. to also allow Vercel preview URLs)
3. Railway redeploys automatically on variable change.

## 5. Test it

Open your Vercel URL on your phone (any network, not just WiFi — it's a
real public URL now), upload a track, confirm the full pipeline runs.

---

## Notes / known limitations of this deployment

- **Ephemeral storage**: uploads, analysis JSON, and the SQLite database
  live on the container's local disk. On Railway this persists across
  requests but **resets on redeploy**. For a demo this is fine — for
  anything longer-lived, attach a Railway Volume mounted at `/app` (Railway
  dashboard → your service → **Volumes**) so `uploads/`, `analysis/`,
  `reports/`, and `backend/rawform.db` survive redeploys.
- **Large file uploads**: the app allows up to 500MB per the spec. Some
  hosts/proxies cap request body size lower by default — if a large upload
  fails on Railway/Render, check that host's request-size settings.
- **Cold starts**: the first request after the container has been idle will
  be slower (loading librosa/numba). Later requests are fast. This is
  normal for this kind of workload on any host.
- **Render / Fly.io alternative**: both also auto-detect a root
  `Dockerfile`. Render's free tier spins the service down after 15 minutes
  of inactivity (slow ~30-60s cold start on the next request) — fine for an
  occasional demo, less fine if you want it always warm. Railway's usage-based
  pricing keeps it running continuously without that penalty.
