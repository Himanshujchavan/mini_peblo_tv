import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { ArtworkOut, Episode, Season, Show } from "../types";
import ArtworkSlot from "../components/ArtworkSlot";

const SECTIONS = ["featured", "series", "minisodes", "songs"];
const CATEGORIES = [
  "adventure", "folk", "friendship", "india", "language", "learning", "maths",
  "music", "nature", "reading", "science", "singalong", "stories", "travel", "values",
];
const LANGUAGES = ["en", "hi"];

export default function ShowEditor() {
  const { showId } = useParams();
  const qc = useQueryClient();

  const showQuery = useQuery({ queryKey: ["show", showId], queryFn: () => api<Show>(`/admin/shows/${showId}`) });
  const seasonsQuery = useQuery({
    queryKey: ["seasons", showId],
    queryFn: () => api<Season[]>(`/admin/shows/${showId}/seasons`),
  });
  const artworkQuery = useQuery({
    queryKey: ["show-artwork", showId],
    queryFn: () => api<ArtworkOut[]>(`/admin/shows/${showId}/artwork`),
  });

  const [form, setForm] = useState<Partial<Show> | null>(null);
  const show = form ?? showQuery.data;

  const saveShow = useMutation({
    mutationFn: (patch: Partial<Show>) =>
      api<Show>(`/admin/shows/${showId}`, { method: "PATCH", body: JSON.stringify(patch) }),
    onSuccess: (updated) => {
      qc.setQueryData(["show", showId], updated);
      setForm(null);
    },
  });

  const addSeason = useMutation({
    mutationFn: (number: number) =>
      api<Season>(`/admin/shows/${showId}/seasons`, { method: "POST", body: JSON.stringify({ number }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["seasons", showId] }),
  });

  if (showQuery.isLoading) return <div className="spinner-text">Loading show...</div>;
  if (showQuery.isError || !show) return <div className="callout callout-error">Couldn't load this show.</div>;

  const posterArt = artworkQuery.data?.find((a) => a.kind === "poster");
  const bannerArt = artworkQuery.data?.find((a) => a.kind === "banner");

  return (
    <div>
      <h1 className="page-title">{show.title}</h1>
      <p className="page-sub">
        <span className={`badge badge-${show.status}`}>{show.status}</span>
      </p>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Details</h3>
        <div className="form-grid">
          <div className="form-field">
            <label>Title</label>
            <input
              className="input"
              value={form?.title ?? show.title}
              onChange={(e) => setForm({ ...show, title: e.target.value })}
            />
          </div>
          <div className="form-field">
            <label>Categories</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px 14px", padding: "8px 0" }}>
              {CATEGORIES.map((cat) => {
                const current = form?.categories ?? show.categories ?? [];
                const checked = current.includes(cat);
                return (
                  <label key={cat} style={{ display: "flex", alignItems: "center", gap: 4, fontWeight: 400 }}>
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        const next = e.target.checked
                          ? [...current, cat]
                          : current.filter((c) => c !== cat);
                        setForm({ ...show, categories: next });
                      }}
                    />
                    {cat}
                  </label>
                );
              })}
            </div>
            <span className="hint">Pick at least one — shows can belong to several categories.</span>
          </div>
          <div className="form-field">
            <label>Section</label>
            <select
              className="input"
              value={form?.section ?? show.section ?? ""}
              onChange={(e) => setForm({ ...show, section: e.target.value || null })}
            >
              <option value="">No section (can't publish)</option>
              {SECTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <span className="hint">Required before this show can be published.</span>
          </div>
          <div className="form-field">
            <label>Status</label>
            <select
              className="input"
              value={form?.status ?? show.status}
              onChange={(e) => setForm({ ...show, status: e.target.value as any })}
            >
              <option value="draft">Draft</option>
              <option value="published">Published</option>
            </select>
          </div>
          <div className="form-field" style={{ gridColumn: "1 / -1" }}>
            <label>Synopsis</label>
            <textarea
              className="input"
              rows={3}
              value={form?.synopsis ?? show.synopsis}
              onChange={(e) => setForm({ ...show, synopsis: e.target.value })}
            />
          </div>
        </div>
        {saveShow.isError && (
          <div className="callout callout-error" style={{ marginTop: 12 }}>
            {(saveShow.error as Error).message}
          </div>
        )}
        <div className="toolbar" style={{ marginTop: 14 }}>
          <button
            className="btn btn-primary"
            disabled={!form || saveShow.isPending}
            onClick={() => form && saveShow.mutate(form)}
          >
            {saveShow.isPending ? "Saving..." : "Save changes"}
          </button>
          {form && <button className="btn" onClick={() => setForm(null)}>Cancel</button>}
        </div>
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Artwork</h3>
        <div className="artwork-slots">
          <ArtworkSlot kind="poster" showId={showId} current={posterArt} onUploaded={() => qc.invalidateQueries({ queryKey: ["show-artwork", showId] })} />
          <ArtworkSlot kind="banner" showId={showId} current={bannerArt} onUploaded={() => qc.invalidateQueries({ queryKey: ["show-artwork", showId] })} />
        </div>
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Seasons &amp; episodes</h3>
        <p className="page-sub">Season 0 is reserved for trailers and won't appear as a normal season to viewers.</p>
        {seasonsQuery.data?.map((season) => (
          <SeasonBlock key={season.id} season={season} />
        ))}
        <AddSeasonForm onAdd={(n) => addSeason.mutate(n)} pending={addSeason.isPending} />
      </div>
    </div>
  );
}

function AddSeasonForm({ onAdd, pending }: { onAdd: (n: number) => void; pending: boolean }) {
  const [number, setNumber] = useState(1);
  return (
    <div className="toolbar">
      <input
        className="input"
        style={{ minWidth: 100 }}
        type="number"
        min={0}
        value={number}
        onChange={(e) => setNumber(parseInt(e.target.value || "0", 10))}
      />
      <button className="btn" disabled={pending} onClick={() => onAdd(number)}>
        + Add season
      </button>
    </div>
  );
}

function SeasonBlock({ season }: { season: Season }) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const episodesQuery = useQuery({
    queryKey: ["episodes", season.id],
    queryFn: () => api<Episode[]>(`/admin/seasons/${season.id}/episodes`),
    enabled: open,
  });

  const addEpisode = useMutation({
    mutationFn: (body: any) =>
      api<Episode>(`/admin/seasons/${season.id}/episodes`, { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["episodes", season.id] }),
  });

  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: 8, marginBottom: 12 }}>
      <button
        className="btn"
        style={{ width: "100%", textAlign: "left", border: "none", background: "#fafbfe" }}
        onClick={() => setOpen((o) => !o)}
      >
        {season.number === 0 ? "🎬 Trailers (Season 0)" : `Season ${season.number}`} {open ? "▾" : "▸"}
      </button>
      {open && (
        <div style={{ padding: 14 }}>
          {episodesQuery.isLoading && <div className="spinner-text">Loading episodes...</div>}
          {episodesQuery.data && episodesQuery.data.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>#</th><th>Title</th><th>Lang</th><th>Group</th><th>Duration</th><th>Artwork</th><th>Status</th>
                </tr>
              </thead>
              <tbody>
                {episodesQuery.data.map((ep) => (
                  <EpisodeRow key={ep.id} episode={ep} seasonId={season.id} />
                ))}
              </tbody>
            </table>
          )}
          {episodesQuery.data && episodesQuery.data.length === 0 && (
            <p className="page-sub">No episodes yet.</p>
          )}
          <AddEpisodeForm onAdd={(body) => addEpisode.mutate(body)} pending={addEpisode.isPending} error={addEpisode.error as Error | null} />
        </div>
      )}
    </div>
  );
}

function EpisodeRow({ episode, seasonId }: { episode: Episode; seasonId: string }) {
  const qc = useQueryClient();
  const [showArt, setShowArt] = useState(false);
  const thumb = episode.artworks.find((a) => a.kind === "thumbnail");

  const patch = useMutation({
    mutationFn: (body: any) => api<Episode>(`/admin/episodes/${episode.id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["episodes", seasonId] }),
  });

  return (
    <>
      <tr>
        <td>{episode.episode_number}</td>
        <td>{episode.title}</td>
        <td>{episode.language}</td>
        <td>{episode.content_group || "—"}</td>
        <td>{episode.duration_seconds ? `${Math.round(episode.duration_seconds / 60)}m` : "—"}</td>
        <td>
          {thumb ? "✅" : "⚠️ missing"}{" "}
          <button className="btn" style={{ padding: "2px 8px" }} onClick={() => setShowArt((s) => !s)}>
            {showArt ? "hide" : "upload"}
          </button>
        </td>
        <td>
          <select
            className="input"
            value={episode.status}
            onChange={(e) => patch.mutate({ status: e.target.value })}
          >
            <option value="draft">Draft</option>
            <option value="published">Published</option>
          </select>
        </td>
      </tr>
      {patch.isError && (
        <tr>
          <td colSpan={7}><div className="callout callout-error" style={{ margin: "6px 0" }}>{(patch.error as Error).message}</div></td>
        </tr>
      )}
      {showArt && (
        <tr>
          <td colSpan={7}>
            <ArtworkSlot
              kind="thumbnail"
              episodeId={episode.id}
              current={thumb}
              onUploaded={() => qc.invalidateQueries({ queryKey: ["episodes", seasonId] })}
            />
          </td>
        </tr>
      )}
    </>
  );
}

function AddEpisodeForm({ onAdd, pending, error }: { onAdd: (body: any) => void; pending: boolean; error: Error | null }) {
  const [title, setTitle] = useState("");
  const [episodeNumber, setEpisodeNumber] = useState(1);
  const [language, setLanguage] = useState("en");
  const [contentGroup, setContentGroup] = useState("");
  const [duration, setDuration] = useState(600);

  function submit() {
    onAdd({
      title,
      episode_number: episodeNumber,
      language,
      content_group: contentGroup || null,
      duration_seconds: duration,
      status: "draft",
    });
    setTitle("");
  }

  return (
    <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid var(--border)" }}>
      <div className="toolbar">
        <input className="input" placeholder="Episode title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <input className="input" style={{ minWidth: 80 }} type="number" placeholder="#" value={episodeNumber} onChange={(e) => setEpisodeNumber(parseInt(e.target.value || "1", 10))} />
        <select className="input" value={language} onChange={(e) => setLanguage(e.target.value)}>
          {LANGUAGES.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
        <input className="input" placeholder="content_group (optional)" value={contentGroup} onChange={(e) => setContentGroup(e.target.value)} />
        <input className="input" style={{ minWidth: 100 }} type="number" placeholder="seconds" value={duration} onChange={(e) => setDuration(parseInt(e.target.value || "0", 10))} />
        <button className="btn btn-primary" disabled={!title || pending} onClick={submit}>+ Add episode</button>
      </div>
      <p className="hint">Give two episodes the same content_group + different languages to link them as language variants.</p>
      {error && <div className="callout callout-error">{error.message}</div>}
    </div>
  );
}
