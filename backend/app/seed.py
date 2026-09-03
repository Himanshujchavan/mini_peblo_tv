"""
Idempotent seed script, run automatically by docker-compose on first boot
(see backend/entrypoint.sh). Loads data/seed_shows.json — a flat list of
95 episode rows across 8 shows — through the same validation paths the CMS
uses, so whatever's wrong with the seed data surfaces the same way it would
for a real editor.

Two deliberate choices here that matter for the "find the imperfections"
part of the exercise:

1. Rows are inserted with the *status the source data says*, including rows
   that are marked "published" but are missing something publish requires
   (e.g. an episode published with no thumbnail). We do NOT quietly
   downgrade those to draft during seeding — the whole point of the
   validation report is to catch exactly this, so the demo is: seed loads,
   the first publish attempt is blocked, you open the CMS Publish page, see
   why, fix it (upload the missing artwork), and publish succeeds.
2. `artwork_available` on a row is honoured literally — we only generate a
   placeholder image for a kind if that row says it's available. A show's
   poster/banner tends to be declared once (on its first episode row) and
   is unioned across all of that show's rows as they're processed.
"""
import io
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.exc import IntegrityError

from app.database import Base, engine, SessionLocal
from app import models
from app.auth import hash_password
from app.reference import allowed_sections, allowed_categories, allowed_languages, artwork_specs
from app.storage import get_storage
from app.services.publish_service import run_publish, PublishBlocked

SEED_PATH = Path("/data/seed_shows.json")
if not SEED_PATH.is_file():
    SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "seed_shows.json"

PALETTE = ["#FF6B6B", "#4ECDC4", "#FFD93D", "#6C5CE7", "#FF9F43", "#1DD1A1", "#54A0FF", "#F368E0"]


def make_placeholder(width: int, height: int, label: str, color: str) -> bytes:
    img = Image.new("RGB", (width, height), color)
    draw = ImageDraw.Draw(img)
    for _ in range(4):
        r = random.randint(20, min(width, height) // 4)
        x, y = random.randint(0, width), random.randint(0, height)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=random.choice(PALETTE))
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.rectangle([0, height - 40, width, height], fill="#00000088")
    draw.text((10, height - 32), label[:24], fill="white", font=font)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()


def ensure_users(db):
    demo_users = [
        ("editor@peblo.tv", "editor123", models.Role.editor),
        ("admin@peblo.tv", "admin123", models.Role.admin),
    ]
    for email, pw, role in demo_users:
        if not db.query(models.User).filter_by(email=email).first():
            db.add(models.User(email=email, hashed_password=hash_password(pw), role=role))
    db.commit()


def _place_show_artwork(storage, show: models.Show, kind: str, color: str):
    specs = artwork_specs()
    w, h = specs[kind]["target_px"]
    key = f"artwork/{show.id}/{kind}-seed.jpg"
    data = make_placeholder(w, h, show.title, color)
    storage.write_bytes(key, data)
    return models.Artwork(show_id=show.id, kind=kind, storage_key=key, width=w, height=h, size_bytes=len(data))


def _place_episode_thumbnail(storage, ep: models.Episode, color: str):
    specs = artwork_specs()
    w, h = specs["thumbnail"]["target_px"]
    key = f"artwork/{ep.id}/thumbnail-seed.jpg"
    data = make_placeholder(w, h, ep.title, color)
    storage.write_bytes(key, data)
    return models.Artwork(episode_id=ep.id, kind="thumbnail", storage_key=key, width=w, height=h, size_bytes=len(data))


def load_seed(db):
    with open(SEED_PATH) as f:
        rows = json.load(f)

    sections = set(allowed_sections())
    categories_ok = set(allowed_categories())
    languages_ok = set(allowed_languages())

    rejected = []
    show_cache: dict[str, models.Show] = {}
    show_color: dict[str, str] = {}
    show_artwork_kinds: dict[str, set] = {}
    season_cache: dict[tuple, models.Season] = {}
    storage = get_storage()

    for row in rows:
        show_title = row["show_title"]

        if show_title not in show_cache:
            bad_cats = set(row["categories"]) - categories_ok
            if bad_cats:
                rejected.append({"row": row, "reason": f"unknown categories {sorted(bad_cats)}"})
                continue
            section = row.get("section")
            if section and section not in sections:
                rejected.append({"row": row, "reason": f"section '{section}' not in reference.json — show created without a section"})
                section = None

            show = models.Show(
                title=show_title, synopsis=row.get("synopsis", ""),
                categories=row["categories"], section=section, status=models.Status.draft,
            )
            db.add(show)
            db.flush()
            show_cache[show_title] = show
            show_color[show_title] = random.choice(PALETTE)
            show_artwork_kinds[show_title] = set()

        show = show_cache[show_title]

        # union show-level artwork (poster/banner) across every row for this show
        new_show_kinds = (set(row.get("artwork_available", [])) & {"poster", "banner"}) - show_artwork_kinds[show_title]
        for kind in new_show_kinds:
            db.add(_place_show_artwork(storage, show, kind, show_color[show_title]))
        show_artwork_kinds[show_title] |= new_show_kinds

        season_key = (show.id, row["season_number"])
        if season_key not in season_cache:
            season = models.Season(show_id=show.id, number=row["season_number"])
            db.add(season)
            db.flush()
            season_cache[season_key] = season
        season = season_cache[season_key]

        if row["language"] not in languages_ok:
            rejected.append({"row": row, "reason": f"language '{row['language']}' not in reference.json allowed languages"})
            continue

        ep = models.Episode(
            season_id=season.id,
            title=row["episode_title"],
            episode_number=row["episode_number"],
            duration_seconds=row.get("duration_seconds"),
            language=row["language"],
            content_group=row.get("content_group"),
            status=row["status"],  # verbatim — see module docstring
        )
        # SAVEPOINT: a duplicate (content_group, language) must only undo this
        # one insert, not every uncommitted row staged earlier in the loop.
        try:
            with db.begin_nested():
                db.add(ep)
                db.flush()
        except IntegrityError:
            rejected.append({"row": row, "reason": "duplicate (content_group, language) — a language variant of this episode already exists"})
            continue

        if "thumbnail" in row.get("artwork_available", []):
            db.add(_place_episode_thumbnail(storage, ep, show_color[show_title]))

    db.commit()

    # a show is publish-eligible once it has a section and at least one
    # published episode — whether that publish attempt actually *succeeds*
    # is exactly what the validation report / publish gate decides
    for show in show_cache.values():
        db.refresh(show)
        has_published_ep = any(e.status == models.Status.published for s in show.seasons for e in s.episodes)
        if has_published_ep and show.section:
            show.status = models.Status.published
    db.commit()

    print(f"[seed] loaded {len(show_cache)} shows, rejected {len(rejected)} rows during import:")
    for r in rejected:
        print(f"  - {r['row']['episode_id']} '{r['row'].get('episode_title', '?')}': {r['reason']}")

    return rejected


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_users(db)
        if db.query(models.Show).count() > 0:
            print("[seed] shows already present, skipping data load")
        else:
            load_seed(db)

        admin = db.query(models.User).filter_by(email="admin@peblo.tv").first()
        try:
            run = run_publish(db, triggered_by=admin.email)
            print(f"[seed] initial publish run {run.id}: {run.show_count} shows, {run.episode_count} episode-language rows")
        except PublishBlocked as e:
            print("[seed] initial publish blocked — this is expected: the seed data has "
                  "a deliberately broken published episode. Log in to the CMS as admin@peblo.tv, "
                  "open Publish, fix what's listed (e.g. upload the missing thumbnail), and publish again.")
            for g in e.report.groups:
                print(f"  - {g.rule}: {g.count}")
                for issue in g.issues:
                    print(f"      · {issue.entity_label}: {issue.issue}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
