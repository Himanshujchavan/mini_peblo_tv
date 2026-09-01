const CATEGORY_COLOR_VAR: Record<string, string> = {
  music: "var(--cat-music)",
  singalong: "var(--cat-music)",
  adventure: "var(--cat-adventure)",
  travel: "var(--cat-adventure)",
  learning: "var(--cat-educational)",
  maths: "var(--cat-educational)",
  language: "var(--cat-educational)",
  reading: "var(--cat-educational)",
  science: "var(--cat-science)",
  nature: "var(--cat-science)",
  stories: "var(--cat-fantasy)",
  folk: "var(--cat-fantasy)",
  friendship: "var(--cat-comedy)",
  values: "var(--cat-comedy)",
  india: "var(--cat-adventure)",
};

export function categoryColor(categories: string[]): string {
  for (const c of categories) {
    if (CATEGORY_COLOR_VAR[c]) return CATEGORY_COLOR_VAR[c];
  }
  return "var(--grape)";
}

export function formatDuration(seconds: number | null): string {
  if (!seconds) return "";
  const m = Math.round(seconds / 60);
  return `${m} min`;
}

export const LANGUAGE_LABELS: Record<string, string> = {
  en: "English",
  hi: "हिंदी",
  es: "Español",
  fr: "Français",
};
