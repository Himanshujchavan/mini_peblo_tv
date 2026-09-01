export interface ArtworkRef {
  url: string;
  width: number;
  height: number;
}

export interface EpisodeLanguage {
  language: string;
  episode_id: string;
  duration_seconds: number | null;
}

export interface CatalogueEpisode {
  episode_group_id: string;
  season: number;
  is_trailer: boolean;
  episode_number: number;
  title: string;
  languages: EpisodeLanguage[];
  artwork: Record<string, ArtworkRef>;
}

export interface CatalogueShow {
  show_id: string;
  title: string;
  synopsis: string;
  categories: string[];
  artwork: Record<string, ArtworkRef>;
  episodes: CatalogueEpisode[];
}

export interface CatalogueSection {
  section: string;
  shows: CatalogueShow[];
}

export interface Catalogue {
  generated_at: string;
  run_id: string;
  checksum: string;
  sections: CatalogueSection[];
}

export interface SearchResultShow {
  show_id: string;
  title: string;
  categories: string[];
  section: string;
  artwork: Record<string, ArtworkRef>;
  matched_episode_count: number;
}

export interface SearchResponse {
  query: string | null;
  filters: { category: string | null; language: string | null; section: string | null };
  results: SearchResultShow[];
}
