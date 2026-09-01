from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import auth, shows, episodes, artwork, publish, catalog

settings = get_settings()

app = FastAPI(title="Peblo TV", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the CMS/viewer origins in real prod
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(shows.router)
app.include_router(episodes.router)
app.include_router(artwork.router)
app.include_router(publish.router)
app.include_router(catalog.router)

if settings.storage_backend == "local":
    import os
    os.makedirs(settings.storage_local_path, exist_ok=True)
    app.mount("/static", StaticFiles(directory=settings.storage_local_path), name="static")


@app.get("/health")
def health():
    """
    Liveness + a couple of cheap dependency checks. See README for what we'd
    alert on and why.
    """
    from app.database import SessionLocal
    from sqlalchemy import text
    db_ok = True
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        db_ok = False

    storage_ok = True
    try:
        from app.storage import get_storage
        get_storage()
    except Exception:
        storage_ok = False

    status = "ok" if (db_ok and storage_ok) else "degraded"
    return {"status": status, "database": db_ok, "storage": storage_ok}
