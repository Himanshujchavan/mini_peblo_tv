from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app import models, schemas
from app.auth import require_editor, require_admin, CurrentUser
from app.reference import allowed_categories, allowed_sections

router = APIRouter(prefix="/admin/shows", tags=["shows"])


def _validate_categories(categories: list[str]):
    bad = set(categories) - set(allowed_categories())
    if bad:
        raise HTTPException(422, f"unknown categories {sorted(bad)}; must be from {allowed_categories()}")
    if not categories:
        raise HTTPException(422, "a show needs at least one category")


def _validate_section(section: Optional[str]):
    if section is not None and section not in allowed_sections():
        raise HTTPException(422, f"section must be one of {allowed_sections()}")


@router.get("", response_model=list[schemas.ShowOut])
def list_shows(
    q: Optional[str] = None,
    section: Optional[str] = None,
    status: Optional[str] = None,
    language: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_editor),
):
    query = db.query(models.Show)
    if q:
        query = query.filter(models.Show.title.ilike(f"%{q}%"))
    if section:
        query = query.filter(models.Show.section == section)
    if status:
        query = query.filter(models.Show.status == status)
    if language:
        query = query.join(models.Season).join(models.Episode).filter(models.Episode.language == language).distinct()
    total = query.count()
    items = query.order_by(models.Show.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items


@router.post("", response_model=schemas.ShowOut, status_code=201)
def create_show(body: schemas.ShowCreate, db: Session = Depends(get_db), user: CurrentUser = Depends(require_editor)):
    _validate_categories(body.categories)
    _validate_section(body.section)
    show = models.Show(**body.model_dump())
    db.add(show)
    db.commit()
    db.refresh(show)
    return show


@router.get("/{show_id}", response_model=schemas.ShowOut)
def get_show(show_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(require_editor)):
    show = db.get(models.Show, show_id)
    if not show:
        raise HTTPException(404, "Show not found")
    return show


@router.patch("/{show_id}", response_model=schemas.ShowOut)
def update_show(show_id: str, body: schemas.ShowUpdate, db: Session = Depends(get_db), user: CurrentUser = Depends(require_editor)):
    show = db.get(models.Show, show_id)
    if not show:
        raise HTTPException(404, "Show not found")
    data = body.model_dump(exclude_unset=True)
    if "categories" in data:
        _validate_categories(data["categories"])
    if "section" in data:
        _validate_section(data["section"])
    if data.get("status") == "published" and not (data.get("section") or show.section):
        raise HTTPException(422, "A published show must have a section")
    for k, v in data.items():
        setattr(show, k, v)
    db.commit()
    db.refresh(show)
    return show


@router.delete("/{show_id}", status_code=204)
def delete_show(show_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(require_editor)):
    show = db.get(models.Show, show_id)
    if not show:
        raise HTTPException(404, "Show not found")
    db.delete(show)
    db.commit()
    return None


@router.get("/{show_id}/seasons", response_model=list[schemas.SeasonOut])
def list_seasons(show_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(require_editor)):
    show = db.get(models.Show, show_id)
    if not show:
        raise HTTPException(404, "Show not found")
    return db.query(models.Season).filter_by(show_id=show_id).order_by(models.Season.number).all()


@router.get("/{show_id}/artwork", response_model=list[schemas.ArtworkOut])
def show_artwork(show_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(require_editor)):
    show = db.get(models.Show, show_id)
    if not show:
        raise HTTPException(404, "Show not found")
    return db.query(models.Artwork).filter_by(show_id=show_id, episode_id=None).all()


@router.post("/{show_id}/seasons", response_model=schemas.SeasonOut, status_code=201)
def create_season(show_id: str, body: schemas.SeasonCreate, db: Session = Depends(get_db), user: CurrentUser = Depends(require_editor)):
    show = db.get(models.Show, show_id)
    if not show:
        raise HTTPException(404, "Show not found")
    existing = db.query(models.Season).filter_by(show_id=show_id, number=body.number).first()
    if existing:
        raise HTTPException(409, f"Season {body.number} already exists for this show")
    season = models.Season(show_id=show_id, number=body.number)
    db.add(season)
    db.commit()
    db.refresh(season)
    return season
