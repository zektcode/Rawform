"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchGenres, uploadTrack } from "@/lib/api";
import type { GenreOption } from "@/lib/types";
import { Button } from "@/components/ui";
import { UploadCloud, FileAudio } from "lucide-react";

export default function NewAnalysisPage() {
  const router = useRouter();
  const [genres, setGenres] = useState<GenreOption[]>([]);
  const [genre, setGenre] = useState("techno");
  const [subprofile, setSubprofile] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchGenres()
      .then((g) => {
        setGenres(g);
        if (g[0]) setSubprofile(g[0].default_subprofile);
      })
      .catch(() => setError("Could not reach the analysis backend."));
  }, []);

  const activeGenre = genres.find((g) => g.id === genre);

  function handleGenreChange(nextGenre: string) {
    setGenre(nextGenre);
    const next = genres.find((g) => g.id === nextGenre);
    if (next) setSubprofile(next.default_subprofile);
  }

  async function handleSubmit() {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const res = await uploadTrack(file, genre, subprofile);
      router.push(`/analysis/${res.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed.");
      setUploading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <h1 className="text-[20px] font-semibold text-rf-text tracking-tight mb-1">New Analysis</h1>
      <p className="text-[13px] text-rf-text-dim mb-8">
        Upload a WAV, AIFF, FLAC or MP3 file. Audio is analyzed by your own Rawform backend — never sent to a third-party analysis service.
      </p>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const f = e.dataTransfer.files?.[0];
          if (f) setFile(f);
        }}
        onClick={() => inputRef.current?.click()}
        className={`border border-dashed rounded-sm py-14 flex flex-col items-center justify-center cursor-pointer transition-colors mb-6 ${
          dragOver ? "border-rf-blue bg-rf-blue-dim/5" : "border-rf-border hover:border-rf-text-faint"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".wav,.wave,.aiff,.aif,.flac,.mp3"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        {file ? (
          <>
            <FileAudio size={22} className="text-rf-green mb-3" strokeWidth={1.5} />
            <div className="text-[13px] text-rf-text">{file.name}</div>
            <div className="text-[11px] text-rf-text-faint font-data mt-1">
              {(file.size / (1024 * 1024)).toFixed(1)} MB
            </div>
          </>
        ) : (
          <>
            <UploadCloud size={22} className="text-rf-text-faint mb-3" strokeWidth={1.5} />
            <div className="text-[13px] text-rf-text-dim">Drop a track here, or click to browse</div>
            <div className="text-[11px] text-rf-text-faint mt-1">WAV · AIFF · FLAC · MP3 · up to 500 MB</div>
          </>
        )}
      </div>

      <div className="mb-6">
        <label className="block text-[11px] text-rf-text-dim uppercase tracking-wide mb-2">Select Style</label>
        <div className="grid grid-cols-2 gap-2">
          {(genres.length ? genres : [{ id: "techno", display_name: "Techno" }, { id: "psytrance", display_name: "Psytrance" }]).map((g) => (
            <button
              key={g.id}
              onClick={() => handleGenreChange(g.id)}
              className={`py-3 text-[13px] font-medium border rounded-sm transition-colors ${
                genre === g.id
                  ? "border-rf-blue text-rf-text bg-rf-blue-dim/10"
                  : "border-rf-border text-rf-text-dim hover:text-rf-text hover:border-rf-text-faint"
              }`}
            >
              {g.display_name}
            </button>
          ))}
        </div>
      </div>

      {activeGenre && activeGenre.subprofiles.length > 0 && (
        <div className="mb-8">
          <label className="block text-[11px] text-rf-text-dim uppercase tracking-wide mb-2">
            Subprofile <span className="text-rf-text-faint normal-case">(refines interpretation, not required)</span>
          </label>
          <div className="flex flex-wrap gap-2">
            {activeGenre.subprofiles.map((s) => (
              <button
                key={s.id}
                onClick={() => setSubprofile(s.id)}
                className={`px-3 py-1.5 text-[12px] border rounded-sm transition-colors ${
                  subprofile === s.id
                    ? "border-rf-blue text-rf-text bg-rf-blue-dim/10"
                    : "border-rf-border text-rf-text-dim hover:text-rf-text"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="border border-rf-red-dim bg-rf-red-dim/10 text-rf-red text-[13px] px-4 py-3 mb-6 rounded-sm">
          {error}
        </div>
      )}

      <Button onClick={handleSubmit} disabled={!file || uploading} className="w-full py-2.5">
        {uploading ? "Uploading…" : "Analyze Track"}
      </Button>
    </div>
  );
}
