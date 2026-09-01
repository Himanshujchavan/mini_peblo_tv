"""
Single source of truth for "is this publishable". Both GET /admin/validation-report
and POST /admin/catalog/publish call this — the report an editor sees is exactly
what would block a publish, never a stale approximation of it.

Artwork requirement, spelled out (the brief says "can't publish without artwork"
but doesn't say which of the 3 kinds — we picked the minimum each surface
actually needs, and say so here rather than silently guessing):
  - a SHOW needs `poster` (browse rows) + `banner` (hero) before it can publish
  - an EPISODE needs `thumbnail` (episode list) before it can publish
"""
from sqlalchemy.orm import Session, joinedload

from app import models
from app.reference import allowed_sections, allowed_languages
from app.schemas import ValidationIssue, ValidationGroup, ValidationReport

REQUIRED_SHOW_ARTWORK = {"poster", "banner"}
REQUIRED_EPISODE_ARTWORK = {"thumbnail"}


def build_validation_report(db: Session) -> ValidationReport:
    groups: list[ValidationGroup] = []

    shows = db.query(models.Show).options(
        joinedload(models.Show.artworks),
        joinedload(models.Show.seasons).joinedload(models.Season.episodes).joinedload(models.Episode.artworks),
    ).all()

    sections_ok = set(allowed_sections())
    langs_ok = set(allowed_languages())

    missing_section: list[ValidationIssue] = []
    invalid_section: list[ValidationIssue] = []
    missing_show_artwork: list[ValidationIssue] = []
    missing_episode_artwork: list[ValidationIssue] = []
    missing_duration: list[ValidationIssue] = []
    invalid_language: list[ValidationIssue] = []
    empty_show: list[ValidationIssue] = []  # published show, zero published episodes

    for show in shows:
        if show.status != models.Status.published:
            continue

        if not show.section:
            missing_section.append(ValidationIssue(
                entity_type="show", entity_id=show.id, entity_label=show.title,
                field="section", issue="Published show has no section — pick one so it appears somewhere in the app.",
            ))
        elif show.section not in sections_ok:
            invalid_section.append(ValidationIssue(
                entity_type="show", entity_id=show.id, entity_label=show.title,
                field="section",
                issue=f"Section '{show.section}' isn't one of the allowed sections ({', '.join(sorted(sections_ok))}).",
            ))

        have_kinds = {a.kind.value for a in show.artworks}
        missing = REQUIRED_SHOW_ARTWORK - have_kinds
        if missing:
            missing_show_artwork.append(ValidationIssue(
                entity_type="show", entity_id=show.id, entity_label=show.title,
                field="artwork",
                issue=f"Missing {', '.join(sorted(missing))} artwork — upload it on the show's artwork tab.",
            ))

        published_eps = 0
        for season in show.seasons:
            for ep in season.episodes:
                if ep.status != models.Status.published:
                    continue
                published_eps += 1
                label = f"{show.title} S{season.number}E{ep.episode_number} ({ep.language}) — {ep.title}"

                if ep.duration_seconds is None or ep.duration_seconds <= 0:
                    missing_duration.append(ValidationIssue(
                        entity_type="episode", entity_id=ep.id, entity_label=label,
                        field="duration_seconds", issue="Published episode has no duration set.",
                    ))

                have_ep_kinds = {a.kind.value for a in ep.artworks}
                ep_missing = REQUIRED_EPISODE_ARTWORK - have_ep_kinds
                if ep_missing:
                    missing_episode_artwork.append(ValidationIssue(
                        entity_type="episode", entity_id=ep.id, entity_label=label,
                        field="artwork",
                        issue=f"Missing {', '.join(sorted(ep_missing))} artwork.",
                    ))

                if ep.language not in langs_ok:
                    invalid_language.append(ValidationIssue(
                        entity_type="episode", entity_id=ep.id, entity_label=label,
                        field="language",
                        issue=f"Language '{ep.language}' isn't in the allowed list ({', '.join(sorted(langs_ok))}).",
                    ))

        if published_eps == 0:
            empty_show.append(ValidationIssue(
                entity_type="show", entity_id=show.id, entity_label=show.title,
                issue="Published show has zero published episodes — it would appear empty to viewers.",
            ))

    def add(rule: str, issues: list[ValidationIssue]):
        if issues:
            groups.append(ValidationGroup(rule=rule, count=len(issues), issues=issues))

    add("published_show_missing_section", missing_section)
    add("published_show_invalid_section", invalid_section)
    add("published_show_missing_required_artwork", missing_show_artwork)
    add("published_episode_missing_duration", missing_duration)
    add("published_episode_missing_required_artwork", missing_episode_artwork)
    add("published_episode_invalid_language", invalid_language)
    add("published_show_has_no_published_episodes", empty_show)

    return ValidationReport(can_publish=len(groups) == 0, groups=groups)
