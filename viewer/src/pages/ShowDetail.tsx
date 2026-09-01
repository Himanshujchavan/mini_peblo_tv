import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import type { Catalogue, CatalogueShow } from "../types/catalogue";
import { fetchCatalogue } from "../api/catalog";
import StateBlock from "../components/StateBlock";
import { formatDuration, LANGUAGE_LABELS } from "../components/util";

export default function ShowDetail() {
  const { showId } = useParams();
  const navigate = useNavigate();
  const [catalogue, setCatalogue] = useState<Catalogue | null>(null);
  const [season, setSeason] = useState<number | null>(null);

  useEffect(() => {
    fetchCatalogue().then(setCatalogue).catch(() => setCatalogue(null));
  }, []);

  const show: CatalogueShow | undefined = useMemo(() => {
    if (!catalogue) return undefined;
    for (const s of catalogue.sections) {
      const found = s.shows.find((sh) => sh.show_id === showId);
      if (found) return found;
    }
    return undefined;
  }, [catalogue, showId]);

  if (!catalogue) return <div className="container"><StateBlock title="Loading show..." /></div>;
  if (!show) return <div className="container"><StateBlock title="We can't find that show" subtitle="It might have been unpublished." /></div>;

  const trailer = show.episodes.find((e) => e.is_trailer);
  const normalSeasons = Array.from(
    new Set(show.episodes.filter((e) => !e.is_trailer).map((e) => e.season))
  ).sort((a, b) => a - b);
  const activeSeason = season ?? normalSeasons[0] ?? null;
  const episodesForSeason = show.episodes.filter((e) => !e.is_trailer && e.season === activeSeason);

  return (
    <div className="container">
      <button className="back-link" onClick={() => navigate(-1)}>← Back</button>

      <div className="detail-hero hero" style={{ marginTop: 12 }}>
        {show.artwork.banner?.url && <img className="hero-bg" src={show.artwork.banner.url} alt="" />}
        <div className="hero-scrim" />
        <div className="hero-content">
          <h1 className="hero-title">{show.title}</h1>
          {trailer && (
            <span className="trailer-chip" style={{ display: "inline-block", marginBottom: 10 }}>
              🎬 Trailer available
            </span>
          )}
        </div>
      </div>

      <p className="synopsis-block">{show.synopsis}</p>

      {normalSeasons.length > 0 && (
        <>
          <div className="season-tabs">
            {normalSeasons.map((num) => (
              <button
                key={num}
                className={`season-tab ${activeSeason === num ? "active" : ""}`}
                onClick={() => setSeason(num)}
              >
                Season {num}
              </button>
            ))}
          </div>

          <div className="episode-list">
            {episodesForSeason.map((ep) => (
              <div className="episode-row" key={ep.episode_group_id}>
                <div className="episode-thumb">
                  {ep.artwork.thumbnail?.url && <img src={ep.artwork.thumbnail.url} alt="" loading="lazy" />}
                </div>
                <div className="episode-meta">
                  <p className="episode-title">
                    {ep.episode_number}. {ep.title}
                  </p>
                  <p className="episode-sub">{formatDuration(ep.languages[0]?.duration_seconds ?? null)}</p>
                  <div className="lang-pills">
                    {ep.languages.map((l) => (
                      <span className="lang-pill" key={l.language}>
                        {LANGUAGE_LABELS[l.language] || l.language}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {normalSeasons.length === 0 && !trailer && (
        <StateBlock title="No episodes published yet" subtitle="Check back soon!" />
      )}
    </div>
  );
}
