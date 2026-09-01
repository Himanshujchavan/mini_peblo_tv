import { useNavigate } from "react-router-dom";

interface ShowCardProps {
  id: string;
  title: string;
  imageUrl?: string;
  variant?: "poster" | "thumb";
}

export default function ShowCard({
  id,
  title,
  imageUrl,
  variant = "poster",
}: ShowCardProps) {
  const navigate = useNavigate();
  return (
    <button
      className={`show-card ${variant === "thumb" ? "thumb-card" : ""}`}
      onClick={() => navigate(`/shows/${id}`)}
    >
      <div className="show-card-art">
        {imageUrl ? (
          <img src={imageUrl} alt="" loading="lazy" />
        ) : (
          <div style={{ width: "100%", height: "100%", background: "var(--sky-deep)" }} />
        )}
      </div>
      <div className="show-card-title">{title}</div>
    </button>
  );
}
