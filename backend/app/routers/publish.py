from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import require_editor, require_admin, CurrentUser
from app.services.validation_service import build_validation_report
from app.services.publish_service import run_publish, PublishBlocked

router = APIRouter(prefix="/admin", tags=["publish"])


@router.get("/validation-report", response_model=schemas.ValidationReport)
def validation_report(db: Session = Depends(get_db), user: CurrentUser = Depends(require_editor)):
    return build_validation_report(db)


@router.post("/catalog/publish", response_model=schemas.PublishRunOut, status_code=201)
def publish(db: Session = Depends(get_db), user: CurrentUser = Depends(require_admin)):
    try:
        run = run_publish(db, triggered_by=user.email)
        return run
    except PublishBlocked as e:
        raise HTTPException(
            status_code=422,
            detail={"message": "Publish blocked by validation errors", "report": e.report.model_dump()},
        )


@router.get("/publish-runs", response_model=list[schemas.PublishRunOut])
def publish_runs(db: Session = Depends(get_db), user: CurrentUser = Depends(require_editor)):
    return db.query(models.PublishRun).order_by(models.PublishRun.started_at.desc()).limit(50).all()
