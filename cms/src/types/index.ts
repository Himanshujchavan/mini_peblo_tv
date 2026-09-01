export type Role = "editor" | "admin";

export interface Show {
  id: string;
  title: string;
  synopsis: string;
  categories: string[];
  section: string | null;
  status: "draft" | "published";
  created_at: string;
  updated_at: string;
}

export interface Season {
  id: string;
  show_id: string;
  number: number;
}

export interface ArtworkOut {
  kind: string;
  url: string;
  width: number;
  height: number;
  size_bytes: number;
}

export interface Episode {
  id: string;
  season_id: string;
  title: string;
  episode_number: number;
  duration_seconds: number | null;
  language: string;
  content_group: string | null;
  status: "draft" | "published";
  artworks: ArtworkOut[];
}

export interface ValidationIssue {
  entity_type: string;
  entity_id: string;
  entity_label: string;
  issue: string;
  field?: string;
}

export interface ValidationGroup {
  rule: string;
  count: number;
  issues: ValidationIssue[];
}

export interface ValidationReport {
  can_publish: boolean;
  groups: ValidationGroup[];
}

export interface PublishRun {
  id: string;
  triggered_by: string;
  started_at: string;
  finished_at: string | null;
  outcome: string;
  show_count: number;
  episode_count: number;
  error: string | null;
}
