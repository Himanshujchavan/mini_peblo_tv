import { useEffect, useState } from "react";
import type { Catalogue, CatalogueShow } from "../types/catalogue";
import { fetchCatalogue } from "../api/catalog";
import Hero from "../components/Hero";
import Row from "../components/Row";
import StateBlock from "../components/StateBlock";

const AVAILABLE_CATEGORIES = [
  "adventure",
  "folk",
  "friendship",
  "india",
  "language",
  "learning",
  "maths",
  "music",
  "nature",
  "reading",
  "science",
  "singalong",
  "stories",
  "travel",
  "values",
];

export default function Home() {
  const [catalogue, setCatalogue] = useState<Catalogue | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchCatalogue().then(setCatalogue).catch(() => setError("failed"));
  }, []);

  const toggleCategory = (category: string) => {
    const newSelected = new Set(selectedCategories);
    if (newSelected.has(category)) {
      newSelected.delete(category);
    } else {
      newSelected.add(category);
    }
    setSelectedCategories(newSelected);
  };

  const getFilteredShows = (shows: CatalogueShow[]) => {
    if (selectedCategories.size === 0) return shows;
    return shows.filter((show) =>
      show.categories.some((cat) => selectedCategories.has(cat))
    );
  };

  if (error) {
    return (
      <div className="container">
        <StateBlock
          title="Peblo TV is taking a nap"
          subtitle="We couldn't load any shows right now. Try again in a moment!"
        />
      </div>
    );
  }

  if (!catalogue) {
    return (
      <div className="container">
        <StateBlock title="Getting your shows ready..." />
      </div>
    );
  }

  const allShows = catalogue.sections.flatMap((s) => s.shows);
  const featured = allShows[0];

  if (!featured) {
    return (
      <div className="container">
        <StateBlock
          title="No shows here yet"
          subtitle="Check back soon — new adventures are on the way!"
        />
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: "var(--sky)", minHeight: "100vh" }}>
      {/* Featured Hero */}
      <div className="container">
        <Hero show={featured} />
      </div>

      {/* Main Content */}
      <div className="container" style={{ paddingTop: "2rem", paddingBottom: "2rem" }}>
        {/* Welcome Section */}
        <div style={{ marginBottom: "3rem" }}>
          <h2 style={{
            fontSize: "2rem",
            fontWeight: "800",
            color: "var(--ink)",
            marginBottom: "0.5rem",
            background: "linear-gradient(135deg, #ff6b4a 0%, #7c5cfc 100%)",
            backgroundClip: "text",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}>
            🎬 Discover Your Next Adventure
          </h2>
          <p style={{
            fontSize: "1rem",
            color: "#666",
            marginBottom: "0",
          }}>
            Choose from our amazing collection of shows and minisodes
          </p>
        </div>

        {/* Category Filter Section */}
        <div style={{
          backgroundColor: "rgba(255, 204, 0, 0.08)",
          padding: "1.5rem",
          borderRadius: "16px",
          marginBottom: "3rem",
          border: "2px solid rgba(255, 204, 0, 0.2)",
          backdropFilter: "blur(10px)",
        }}>
          <h3 style={{
            marginBottom: "1rem",
            fontSize: "1.2rem",
            fontWeight: "700",
            color: "var(--ink)",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
          }}>
            🏷️ Filter by Category
          </h3>
          <div style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "0.75rem",
          }}>
            {AVAILABLE_CATEGORIES.map((category) => (
              <button
                key={category}
                onClick={() => toggleCategory(category)}
                style={{
                  padding: "0.6rem 1.2rem",
                  backgroundColor: selectedCategories.has(category) ? "#ffcc00" : "#ffffff",
                  color: selectedCategories.has(category) ? "#000" : "#666",
                  border: selectedCategories.has(category) ? "2px solid #ffb300" : "2px solid #ddd",
                  borderRadius: "25px",
                  cursor: "pointer",
                  fontWeight: selectedCategories.has(category) ? "700" : "500",
                  fontSize: "0.95rem",
                  transition: "all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)",
                  textTransform: "capitalize",
                  boxShadow: selectedCategories.has(category) ? "0 4px 12px rgba(255, 204, 0, 0.3)" : "none",
                  transform: selectedCategories.has(category) ? "scale(1.08)" : "scale(1)",
                }}
                onMouseOver={(e) => {
                  if (!selectedCategories.has(category)) {
                    e.currentTarget.style.backgroundColor = "#f5f5f5";
                    e.currentTarget.style.transform = "scale(1.05)";
                  }
                }}
                onMouseOut={(e) => {
                  if (!selectedCategories.has(category)) {
                    e.currentTarget.style.backgroundColor = "#ffffff";
                    e.currentTarget.style.transform = "scale(1)";
                  }
                }}
              >
                {category}
              </button>
            ))}
          </div>
          {selectedCategories.size > 0 && (
            <button
              onClick={() => setSelectedCategories(new Set())}
              style={{
                marginTop: "1.5rem",
                padding: "0.6rem 1.2rem",
                backgroundColor: "rgba(255, 0, 0, 0.1)",
                color: "#ff6b6b",
                border: "2px solid #ff6b6b",
                borderRadius: "25px",
                cursor: "pointer",
                fontWeight: "600",
                fontSize: "0.95rem",
                transition: "all 0.2s",
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.backgroundColor = "#ff6b6b";
                e.currentTarget.style.color = "white";
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = "rgba(255, 0, 0, 0.1)";
                e.currentTarget.style.color = "#ff6b6b";
              }}
            >
              ✕ Clear All Filters
            </button>
          )}
        </div>

        {/* Shows Grid */}
        <div>
          {catalogue.sections.map((section) => {
            const filteredShows = getFilteredShows(section.shows);
            return filteredShows.length > 0 ? (
              <div key={section.section} style={{ marginBottom: "3rem" }}>
                <Row title={section.section} shows={filteredShows} />
              </div>
            ) : null;
          })}
        </div>

        {/* No Results Message */}
        {selectedCategories.size > 0 && catalogue.sections.every((s) => getFilteredShows(s.shows).length === 0) && (
          <div style={{
            textAlign: "center",
            padding: "3rem 1rem",
            backgroundColor: "rgba(255, 204, 0, 0.05)",
            borderRadius: "16px",
            marginTop: "2rem",
          }}>
            <p style={{ fontSize: "1.1rem", color: "#666", margin: "0" }}>
              😢 No shows found for your selection. Try different categories!
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
