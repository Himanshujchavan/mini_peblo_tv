import { useNavigate } from "react-router-dom";
import type { CatalogueShow } from "../types/catalogue";

export default function Hero({ show }: { show: CatalogueShow }) {
  const navigate = useNavigate();
  const banner = show.artwork.banner?.url;

  return (
    <div className="hero">
      {banner && <img className="hero-bg" src={banner} alt="" />}
      <div className="hero-scrim" />
      <div className="hero-content">
        <span className="hero-badge">New & Trending</span>
        <h1 className="hero-title">{show.title}</h1>
        <p className="hero-synopsis">{show.synopsis}</p>
        <button className="hero-cta" onClick={() => navigate(`/shows/${show.show_id}`)}>
          ▶ Watch now
        </button>
      </div>
    </div>
  );
}
