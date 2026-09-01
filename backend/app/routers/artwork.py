import io
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from PIL import Image
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import require_editor, CurrentUser
from app.storage import get_storage
from app.reference import artwork_specs

router = APIRouter(prefix="/admin/artwork", tags=["artwork"])

# how far off the exact target dimensions we tolerate, and how close the
# aspect ratio must be — editors upload real photos, not exact pixel grids
DIMENSION_TOLERANCE = 0.10
ASPECT_TOLERANCE = 0.02


def _parse_ratio(ratio_str: str) -> float:
    w, h = ratio_str.split(":")
    return int(w) / int(h)


def _validate_image(kind: str, data: bytes) -> tuple[int, int]:
    specs = artwork_specs()
    if kind not in specs:
        raise HTTPException(422, f"Unknown artwork kind '{kind}'. Must be one of {list(specs)}.")
    spec = specs[kind]

    size_kb = len(data) / 1024
    if size_kb > spec["max_kb"]:
        raise HTTPException(
            422,
            f"That {kind} image is {size_kb:.0f} KB — please compress it under {spec['max_kb']} KB "
            "(try re-saving as JPEG at ~80% quality, or resizing).",
        )

    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        img = Image.open(io.BytesIO(data))  # verify() consumes the file; reopen to read size
        width, height = img.size
    except Exception:
        raise HTTPException(422, f"That doesn't look like a valid image file for the {kind} slot.")

    # aspect ratio first: it's the more fundamental mismatch (wrong crop) and
    # gives editors a clearer, single actionable error instead of two at once
    target_ratio = _parse_ratio(spec["aspect"])
    actual_ratio = width / height
    if abs(actual_ratio - target_ratio) / target_ratio > ASPECT_TOLERANCE:
        raise HTTPException(
            422,
            f"{kind.capitalize()} needs a {spec['aspect']} aspect ratio. "
            f"Your image is {width}×{height}px ({actual_ratio:.2f}), which is too "
            f"{'wide' if actual_ratio > target_ratio else 'tall'}. Crop it to {spec['aspect']} and re-upload.",
        )

    target_w, target_h = spec["target_px"]
    lo_w, hi_w = target_w * (1 - DIMENSION_TOLERANCE), target_w * (1 + DIMENSION_TOLERANCE)
    lo_h, hi_h = target_h * (1 - DIMENSION_TOLERANCE), target_h * (1 + DIMENSION_TOLERANCE)
    if not (lo_w <= width <= hi_w and lo_h <= height <= hi_h):
        raise HTTPException(
            422,
            f"{kind.capitalize()} should be about {target_w}×{target_h}px "
            f"(within {int(DIMENSION_TOLERANCE * 100)}%). You uploaded {width}×{height}px — "
            "please resize and try again.",
        )

    return width, height


@router.post("/upload", response_model=schemas.ArtworkUploadResult, status_code=201)
async def upload_artwork(
    kind: str = Form(...),
    show_id: str | None = Form(None),
    episode_id: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_editor),
):
    if not show_id and not episode_id:
        raise HTTPException(422, "Provide either show_id or episode_id")
    if show_id and episode_id:
        raise HTTPException(422, "Provide only one of show_id or episode_id")

    if show_id and not db.get(models.Show, show_id):
        raise HTTPException(404, "Show not found")
    if episode_id and not db.get(models.Episode, episode_id):
        raise HTTPException(404, "Episode not found")

    data = await file.read()
    width, height = _validate_image(kind, data)

    ext = (file.filename or "upload.jpg").rsplit(".", 1)[-1].lower()
    owner_id = show_id or episode_id
    storage_key = f"artwork/{owner_id}/{kind}-{uuid.uuid4().hex[:8]}.{ext}"

    get_storage().write_bytes(storage_key, data)

    existing = db.query(models.Artwork).filter_by(
        show_id=show_id, episode_id=episode_id, kind=kind
    ).first()
    if existing:
        existing.storage_key = storage_key
        existing.width = width
        existing.height = height
        existing.size_bytes = len(data)
        artwork = existing
    else:
        artwork = models.Artwork(
            show_id=show_id, episode_id=episode_id, kind=kind,
            storage_key=storage_key, width=width, height=height, size_bytes=len(data),
        )
        db.add(artwork)
    db.commit()
    db.refresh(artwork)

    return schemas.ArtworkUploadResult(
        kind=kind, url=get_storage().url_for(storage_key),
        width=width, height=height, size_bytes=len(data),
    )
