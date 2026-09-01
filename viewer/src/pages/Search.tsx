import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import type { SearchResultShow } from "../types/catalogue";
import { searchCatalogue } from "../api/catalog";
import ShowCard from "../components/ShowCard";
import StateBlock from "../components/StateBlock";

const CATEGORIES = [
  "adventure", "folk", "friendship", "india", "language", "learning", "maths",
  "music", "nature", "reading", "science", "singalong", "stories", "travel", "values",
];

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "Hindi" },
];

export default function Search() {
  const [params, setParams] = useSearchParams();
  const [results, setResults] = useState<SearchResultShow[] | null>(null);
  const [loading, setLoading] = useState(true);

  const q = params.get("q") || "";
  const category = params.get("category") || "";
  const language = params.get("language") || "";

  useEffect(() => {
    setLoading(true);
    searchCatalogue({ q: q || undefined, category: category || undefined, language: language || undefined })
      .then((r) => setResults(r.results))
      .catch(() => setResults([]))
      .finally(() => setLoading(false));
  }, [q, category, language]);

  function toggleCategory(cat: string) {
    const next = new URLSearchParams(params);
    if (category === cat) next.delete("category");
    else next.set("category", cat);
    setParams(next);
  }

  function toggleLanguage(lang: string) {
    const next = new URLSearchParams(params);
    if (language === lang) next.delete("language");
    else next.set("language", lang);
    setParams(next);
  }

  return (
    <div className="container">
      <h1 className="row-heading" style={{ marginTop: 26 }}>
        {q ? `Results for "${q}"` : "Browse everything"}
      </h1>

      <div className="filter-row">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            className={`filter-pill ${category === cat ? "active" : ""}`}
            onClick={() => toggleCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="filter-row" style={{ marginTop: 12 }}>
        {LANGUAGES.map((lang) => (
          <button
            key={lang.code}
            className={`filter-pill ${language === lang.code ? "active" : ""}`}
            onClick={() => toggleLanguage(lang.code)}
          >
            {lang.label}
          </button>
        ))}
      </div>

      {loading && <StateBlock title="Looking for shows..." />}

      {!loading && results && results.length === 0 && (
        <StateBlock
          title="Nothing here yet!"
          subtitle="Try a different word, or pick another category to explore."
        />
      )}

      {!loading && results && results.length > 0 && (
        <div className="search-grid">
          {results.map((show: SearchResultShow) => (
            <ShowCard key={show.show_id} id={show.show_id} title={show.title} imageUrl={show.artwork.poster?.url} />
          ))}
        </div>
      )}
    </div>
  );
}
