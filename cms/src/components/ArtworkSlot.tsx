import { useRef, useState } from "react";
import { API_BASE, getToken } from "../api/client";
import type { ArtworkOut } from "../types";

const SPECS: Record<string, string> = {
  poster: "600×900px, 2:3",
  banner: "1280×720px, 16:9",
  thumbnail: "640×360px, 16:9",
};

export default function ArtworkSlot({
  kind,
  showId,
  episodeId,
  current,
  onUploaded,
}: {
  kind: "poster" | "banner" | "thumbnail";
  showId?: string;
  episodeId?: string;
  current?: ArtworkOut;
  onUploaded: (art: ArtworkOut) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(current?.url || null);

  async function handleFile(file: File) {
    setError(null);
    setUploading(true);
    setPreviewUrl(URL.createObjectURL(file));

    const form = new FormData();
    form.set("kind", kind);
    if (showId) form.set("show_id", showId);
    if (episodeId) form.set("episode_id", episodeId);
    form.set("file", file);

    try {
      const res = await fetch(`${API_BASE}/admin/artwork/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
        body: form,
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || "Upload failed");
      onUploaded(body as ArtworkOut);
      setPreviewUrl(body.url);
    } catch (e: any) {
      setError(e.message);
      setPreviewUrl(current?.url || null);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="artwork-slot">
      <div style={{ fontWeight: 700, marginBottom: 4, textTransform: "capitalize" }}>{kind}</div>
      <div className="spec">{SPECS[kind]}, under 300KB</div>
      {previewUrl && <img src={previewUrl} alt={`${kind} preview`} />}
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        style={{ display: "none" }}
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
      />
      <button className="btn" style={{ width: "100%" }} onClick={() => inputRef.current?.click()} disabled={uploading}>
        {uploading ? "Uploading..." : previewUrl ? "Replace" : "Upload"}
      </button>
      {error && <div className="error">{error}</div>}
    </div>
  );
}
