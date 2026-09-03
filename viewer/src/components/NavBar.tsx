import { useNavigate, useSearchParams } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";

export default function NavBar() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [q, setQ] = useState(params.get("q") || "");
  const activeLang = params.get("language") || "";
  const { user } = useAuth();
  const { theme } = useTheme();

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
    navigate(`${location.pathname === "/search" ? "/search" : "/"}?${next.toString()}`);
  }

  return (
    <nav
      style={{
        backgroundColor: theme === "dark" ? "#0f0f0f" : "#ffffff",
        borderBottom: theme === "dark" ? "2px solid #333" : "2px solid #f0f0f0",
        padding: "0.75rem 0",
        boxShadow: theme === "dark" ? "0 2px 8px rgba(0,0,0,0.3)" : "0 2px 8px rgba(0,0,0,0.1)",
        position: "sticky",
        top: 0,
        zIndex: 100,
        transition: "all 0.3s ease",
      }}
    >
      <div
        style={{
          maxWidth: "1180px",
          margin: "0 auto",
          padding: "0 20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "1.5rem",
          flexWrap: "wrap",
        }}
      >
        {/* Logo & Brand */}
        <div
          onClick={() => navigate("/")}
          style={{
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            fontSize: "1.5rem",
            fontWeight: "800",
            color: theme === "dark" ? "#fff" : "#000",
            textDecoration: "none",
            userSelect: "none",
            transition: "all 0.2s",
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.transform = "scale(1.05)";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = "scale(1)";
          }}
        >
          <span style={{ fontSize: "2rem" }}>🎬</span>
          <span>Peblo TV</span>
        </div>

        {/* Search Bar */}
        <form
          onSubmit={submitSearch}
          style={{
            flex: "1 1 250px",
            minWidth: "250px",
            maxWidth: "400px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              backgroundColor: theme === "dark" ? "#1a1a1a" : "#f5f5f5",
              border: theme === "dark" ? "2px solid #333" : "2px solid #e0e0e0",
              borderRadius: "24px",
              padding: "0.5rem 1rem",
              transition: "all 0.3s",
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.borderColor = "#ffcc00";
              e.currentTarget.style.boxShadow = "0 0 8px rgba(255, 204, 0, 0.2)";
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.borderColor = theme === "dark" ? "#333" : "#e0e0e0";
              e.currentTarget.style.boxShadow = "none";
            }}
          >
            <span style={{ fontSize: "1.2rem" }}>🔍</span>
            <input
              type="search"
              placeholder="Find a show..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
              style={{
                border: "none",
                backgroundColor: "transparent",
                color: theme === "dark" ? "#fff" : "#000",
                fontSize: "0.95rem",
                outline: "none",
                width: "100%",
                fontFamily: "inherit",
              }}
            />
          </div>
        </form>

        {/* Right Controls */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "1rem",
            justifyContent: "flex-end",
          }}
        >
          {/* Language Toggle */}
          <div
            style={{
              display: "flex",
              gap: "0.5rem",
              backgroundColor: theme === "dark" ? "#1a1a1a" : "#f5f5f5",
              padding: "0.25rem",
              borderRadius: "20px",
              border: theme === "dark" ? "1px solid #333" : "1px solid #ddd",
            }}
          >
            {["en", "hi"].map((lang) => (
              <button
                key={lang}
                onClick={() => setLanguage(lang)}
                style={{
                  padding: "0.5rem 0.9rem",
                  backgroundColor: activeLang === lang ? "#ffcc00" : "transparent",
                  color: activeLang === lang ? "#000" : theme === "dark" ? "#fff" : "#666",
                  border: "none",
                  borderRadius: "18px",
                  cursor: "pointer",
                  fontWeight: activeLang === lang ? "700" : "600",
                  fontSize: "0.85rem",
                  transition: "all 0.2s",
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                }}
                onMouseOver={(e) => {
                  if (activeLang !== lang) {
                    e.currentTarget.style.backgroundColor = theme === "dark" ? "#333" : "#e0e0e0";
                  }
                }}
                onMouseOut={(e) => {
                  if (activeLang !== lang) {
                    e.currentTarget.style.backgroundColor = "transparent";
                  }
                }}
              >
                {lang}
              </button>
            ))}
          </div>

          {/* Profile & Settings Buttons */}
          {user && (
            <>
              <button
                onClick={() => navigate("/profile")}
                style={{
                  backgroundColor: "#ffcc00",
                  color: "#000",
                  border: "none",
                  borderRadius: "20px",
                  padding: "0.6rem 1.2rem",
                  cursor: "pointer",
                  fontSize: "0.9rem",
                  fontWeight: "700",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  transition: "all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)",
                  boxShadow: "0 4px 12px rgba(255, 204, 0, 0.3)",
                  whiteSpace: "nowrap",
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.transform = "translateY(-2px)";
                  e.currentTarget.style.boxShadow = "0 6px 16px rgba(255, 204, 0, 0.4)";
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "0 4px 12px rgba(255, 204, 0, 0.3)";
                }}
              >
                👤 Profile
              </button>

              <button
                onClick={() => navigate("/settings")}
                style={{
                  backgroundColor: theme === "dark" ? "#1a1a1a" : "#f5f5f5",
                  color: theme === "dark" ? "#fff" : "#666",
                  border: theme === "dark" ? "2px solid #333" : "2px solid #ddd",
                  borderRadius: "20px",
                  padding: "0.6rem 1.2rem",
                  cursor: "pointer",
                  fontSize: "0.9rem",
                  fontWeight: "600",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  transition: "all 0.2s",
                  whiteSpace: "nowrap",
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.transform = "scale(1.08)";
                  e.currentTarget.style.borderColor = "#ffcc00";
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.transform = "scale(1)";
                  e.currentTarget.style.borderColor = theme === "dark" ? "#333" : "#ddd";
                }}
              >
                ⚙️ Settings
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
