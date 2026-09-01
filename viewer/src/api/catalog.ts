import type { Catalogue, SearchResponse } from "../types/catalogue";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function fetchCatalogue(): Promise<Catalogue> {
  const res = await fetch(`${API_BASE}/catalog`);
  if (!res.ok) throw new Error(`Catalogue fetch failed: ${res.status}`);
  return res.json();
}

export async function searchCatalogue(params: {
  q?: string;
  category?: string;
  language?: string;
  section?: string;
}): Promise<SearchResponse> {
  const qs = new URLSearchParams();
  if (params.q) qs.set("q", params.q);
  if (params.category) qs.set("category", params.category);
  if (params.language) qs.set("language", params.language);
  if (params.section) qs.set("section", params.section);
  const res = await fetch(`${API_BASE}/catalog/search?${qs.toString()}`);
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}
