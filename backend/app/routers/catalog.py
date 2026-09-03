import json
from typing import Optional
from fastapi import APIRouter, HTTPException

from app.storage import get_storage

router = APIRouter(tags=["catalog"])

POINTER_KEY = "catalogue/current.json"


def _load_catalogue() -> dict:
    storage = get_storage()
    if not storage.exists(POINTER_KEY):
        raise HTTPException(503, "Catalogue has not been published yet")
    return json.loads(storage.read_bytes(POINTER_KEY))


@router.get("/catalog")
def get_catalog():
    """What the viewer app reads. Served straight from the pre-built file —
    no DB query per request. See README for the trade-offs of that choice."""
    return _load_catalogue()


@router.get("/catalog/search")
def search_catalog(
    q: Optional[str] = None,
    category: Optional[str] = None,
    language: Optional[str] = None,
    section: Optional[str] = None,
):
    """
    In-memory filter over the already-small published catalogue. Fine at this
    scale (see README for where this stops being fine and what replaces it).
    All filters compose (AND).
    """
    catalogue = _load_catalogue()
    q_lower = (q or "").strip().lower()

    results = []
    for sec in catalogue["sections"]:
        if section and sec["section"] != section:
            continue
        for show in sec["shows"]:
            if category and category not in show["categories"]:
                continue

            show_title_match = q_lower in show["title"].lower() if q_lower else True
            category_match = any(q_lower in c.lower() for c in show["categories"]) if q_lower else False

            matched_episodes = []
            for ep in show["episodes"]:
                ep_title_match = q_lower in ep["title"].lower() if q_lower else False
                langs = ep["languages"]
                if language:
                    langs = [language_entry for language_entry in langs if language_entry["language"] == language]
                    if not langs:
                        continue
                if q_lower and not (show_title_match or category_match or ep_title_match):
                    continue
                matched_episodes.append({**ep, "languages": langs})

            if q_lower and not (show_title_match or category_match) and not matched_episodes:
                continue
            if language and not matched_episodes and not show_title_match:
                continue

            results.append({
                "show_id": show["show_id"],
                "title": show["title"],
                "categories": show["categories"],
                "section": sec["section"],
                "artwork": show["artwork"],
                "matched_episode_count": len(matched_episodes) if q_lower or language else len(show["episodes"]),
            })

    return {"query": q, "filters": {"category": category, "language": language, "section": section}, "results": results}
