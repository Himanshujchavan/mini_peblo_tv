import { useNavigate, useSearchParams } from "react-router-dom";
import { useState } from "react";

export default function NavBar() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [q, setQ] = useState(params.get("q") || "");
  const activeLang = params.get("language") || "";

  function submitSearch(e: React.FormEvent) {
    e.preventDefault();
    const next = new URLSearchParams();
    if (q.trim()) next.set("q", q.trim());
    navigate(`/search?${next.toString()}`);
  }

  function setLanguage(lang: string) {
    const next = new URLSearchParams(params);
    if (lang) next.set("language", lang);
    else next.delete("language");
    navigate(`${location.pathname === "/search" ? "/search" : "/search"}?${next.toString()}`);
  }

  return (
    <nav className="nav">
      <a className="brand" href="/" onClick={(e) => { e.preventDefault(); navigate("/"); }}>
        <span className="brand-blob" aria-hidden="true" />
        Peblo TV
      </a>

      <form className="nav-search" onSubmit={submitSearch} role="search">
        <span aria-hidden="true">🔍</span>
        <input
          type="search"
          placeholder="Find a show..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search shows"
        />
      </form>

      <div className="lang-toggle" role="group" aria-label="Language">
        {["en", "hi"].map((lang) => (
          <button
            key={lang}
            className={activeLang === lang ? "active" : ""}
            onClick={() => setLanguage(lang)}
          >
            {lang.toUpperCase()}
          </button>
        ))}
      </div>
    </nav>
  );
}
