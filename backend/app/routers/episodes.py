from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import require_editor, CurrentUser
from app.reference import allowed_languages
from app.services.validation_service import REQUIRED_EPISODE_ARTWORK

router = APIRouter(tags=["episodes"])


def _validate_language(lang: str):
    if lang not in allowed_languages():
        raise HTTPException(422, f"language must be one of {allowed_languages()}")


@router.get("/admin/seasons/{season_id}/episodes", response_model=list[schemas.EpisodeOut])
def list_episodes(season_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(require_editor)):
    season = db.get(models.Season, season_id)
    if not season:
        raise HTTPException(404, "Season not found")
    return db.query(models.Episode).filter_by(season_id=season_id).order_by(models.Episode.episode_number).all()


@router.post("/admin/seasons/{season_id}/episodes", response_model=schemas.EpisodeOut, status_code=201)
def create_episode(season_id: str, body: schemas.EpisodeCreate, db: Session = Depends(get_db), user: CurrentUser = Depends(require_editor)):
    season = db.get(models.Season, season_id)
    if not season:
        raise HTTPException(404, "Season not found")
    _validate_language(body.language)

    ep = models.Episode(season_id=season_id, **body.model_dump())
    db.add(ep)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409,
            f"An episode with content_group='{body.content_group}' and language='{body.language}' "
            "already exists — language variants of the same episode must be unique per language.",
        )
    db.refresh(ep)
    return ep


@router.patch("/admin/episodes/{episode_id}", response_model=schemas.EpisodeOut)
def update_episode(episode_id: str, body: schemas.EpisodeUpdate, db: Session = Depends(get_db), user: CurrentUser = Depends(require_editor)):
    ep = db.get(models.Episode, episode_id)
    if not ep:
        raise HTTPException(404, "Episode not found")
    data = body.model_dump(exclude_unset=True)
    if "language" in data:
        _validate_language(data["language"])

    going_published = data.get("status") == "published"
    if going_published:
        duration = data.get("duration_seconds", ep.duration_seconds)
        if not duration or duration <= 0:
            raise HTTPException(422, "Cannot publish an episode without a duration")
        have_kinds = {a.kind.value for a in ep.artworks}
        if not REQUIRED_EPISODE_ARTWORK.issubset(have_kinds):
            missing = REQUIRED_EPISODE_ARTWORK - have_kinds
            raise HTTPException(422, f"Cannot publish an episode missing artwork: {', '.join(missing)}")

    for k, v in data.items():
        setattr(ep, k, v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "That (content_group, language) combination already exists")
    db.refresh(ep)
    return ep


@router.delete("/admin/episodes/{episode_id}", status_code=204)
def delete_episode(episode_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(require_editor)):
    ep = db.get(models.Episode, episode_id)
    if not ep:
        raise HTTPException(404, "Episode not found")
    db.delete(ep)
    db.commit()
    return None
