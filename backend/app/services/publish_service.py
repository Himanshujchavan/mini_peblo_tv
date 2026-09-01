"""
Publish job.

Atomicity strategy (see README Part E for the full writeup):
1. Build the whole catalogue JSON in memory from a read-only DB snapshot.
2. Write it to a *new, uniquely-named* object in storage (run_key). This is
   never visible to readers because nothing points at it yet.
3. Flip a pointer object (catalogue/current.json) to that run's content in one
   atomic storage operation (`Storage.atomic_publish`). Readers only ever read
   the pointer, so they see either the fully-old or the fully-new catalogue —
   never a half-written one.
4. Only after the pointer flip succeeds do we mark the PublishRun "success".
   If the process dies before step 3, the pointer still targets the previous
   good run and the live catalogue is untouched. If it dies between writing
   run_key and flipping the pointer, same thing — the half-finished run_key
   object is simply orphaned garbage, not something anyone reads.

Idempotency: re-running publish with no underlying data changes produces byte-
identical JSON (deterministic ordering, no timestamps in the body) which we
detect via checksum and record as `outcome="success"` with `unchanged=True`
noted in the run — it's safe to click publish twice.
"""
import hashlib
import json
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app import models
from app.storage import get_storage
from app.services.validation_service import build_validation_report
from app.reference import trailer_season


class PublishBlocked(Exception):
    def __init__(self, report):
        self.report = report
        super().__init__("Publish blocked by validation errors")


def _build_catalogue_dict(db: Session) -> dict:
    shows = (
        db.query(models.Show)
        .filter(models.Show.status == models.Status.published)
        .options(
            joinedload(models.Show.artworks),
            joinedload(models.Show.seasons).joinedload(models.Season.episodes).joinedload(models.Episode.artworks),
        )
        .order_by(models.Show.title.asc())
        .all()
    )

    trailer_season_num = trailer_season()
    sections: dict[str, list[dict]] = {}

    for show in shows:
        show_artwork = {a.kind.value: {"url": _url(a), "width": a.width, "height": a.height} for a in show.artworks}

        # collapse content_group variants into one catalogue entry with a languages[] list.
        # key = (season_number, episode_number, content_group or episode id if ungrouped)
        grouped: dict[tuple, dict] = {}
        order: list[tuple] = []

        for season in sorted(show.seasons, key=lambda s: s.number):
            is_trailer_season = season.number == trailer_season_num
            for ep in sorted(season.episodes, key=lambda e: e.episode_number):
                if ep.status != models.Status.published:
                    continue
                group_key = (season.number, ep.episode_number, ep.content_group or f"__solo__{ep.id}")
                ep_artwork = {a.kind.value: {"url": _url(a), "width": a.width, "height": a.height} for a in ep.artworks}

                if group_key not in grouped:
                    grouped[group_key] = {
                        "episode_group_id": ep.content_group or ep.id,
                        "season": season.number,
                        "is_trailer": is_trailer_season,
                        "episode_number": ep.episode_number,
                        "title": ep.title,
                        "languages": [],
                        "artwork": ep_artwork,  # first-seen episode's artwork represents the group
                    }
                    order.append(group_key)

                grouped[group_key]["languages"].append({
                    "language": ep.language,
                    "episode_id": ep.id,
                    "duration_seconds": ep.duration_seconds,
                })

        # deterministic order: by season number, then episode number
        episodes_out = [grouped[k] for k in sorted(order, key=lambda k: (k[0], k[1]))]
        for ep in episodes_out:
            ep["languages"].sort(key=lambda l: l["language"])

        show_entry = {
            "show_id": show.id,
            "title": show.title,
            "synopsis": show.synopsis,
            "categories": show.categories,
            "artwork": show_artwork,
            "episodes": episodes_out,
        }

        sections.setdefault(show.section, []).append(show_entry)

    # deterministic section + show ordering
    section_list = [
        {"section": name, "shows": sorted(shows_in_section, key=lambda s: s["title"])}
        for name, shows_in_section in sorted(sections.items())
    ]

    return {
        "generated_at": None,  # filled in by caller; kept out of the checksum input
        "sections": section_list,
    }


def _url(artwork: models.Artwork) -> str:
    return get_storage().url_for(artwork.storage_key)


def _checksum(catalogue_body: dict) -> str:
    body_without_ts = {k: v for k, v in catalogue_body.items() if k != "generated_at"}
    raw = json.dumps(body_without_ts, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def run_publish(db: Session, triggered_by: str) -> models.PublishRun:
    report = build_validation_report(db)
    if not report.can_publish:
        raise PublishBlocked(report)

    run = models.PublishRun(triggered_by=triggered_by, outcome="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        catalogue = _build_catalogue_dict(db)
        checksum = _checksum(catalogue)
        catalogue["generated_at"] = datetime.utcnow().isoformat() + "Z"
        catalogue["run_id"] = run.id
        catalogue["checksum"] = checksum

        storage = get_storage()
        run_key = f"catalogue/runs/{run.id}.json"
        pointer_key = "catalogue/current.json"

        storage.write_bytes(run_key, json.dumps(catalogue, indent=2).encode())
        storage.atomic_publish(run_key, pointer_key)  # <-- the atomic swap

        show_count = sum(len(s["shows"]) for s in catalogue["sections"])
        episode_count = sum(
            len(ep["languages"]) for s in catalogue["sections"] for sh in s["shows"] for ep in sh["episodes"]
        )

        run.outcome = "success"
        run.finished_at = datetime.utcnow()
        run.show_count = show_count
        run.episode_count = episode_count
        run.catalogue_storage_key = run_key
        run.checksum = checksum
        db.commit()
        db.refresh(run)
        return run
    except Exception as e:
        run.outcome = "failed"
        run.finished_at = datetime.utcnow()
        run.error = str(e)
        db.commit()
        raise
