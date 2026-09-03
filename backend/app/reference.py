import json
import os
from functools import lru_cache
from pathlib import Path

REFERENCE_PATH = Path(os.environ.get("REFERENCE_JSON_PATH", "/data/reference.json"))
if not REFERENCE_PATH.is_file() and "REFERENCE_JSON_PATH" not in os.environ:
    REFERENCE_PATH = Path(__file__).resolve().parents[2] / "data" / "reference.json"


@lru_cache
def get_reference() -> dict:
    with open(REFERENCE_PATH) as f:
        return json.load(f)


def allowed_sections() -> list[str]:
    return get_reference()["sections"]


def allowed_categories() -> list[str]:
    return get_reference()["categories"]


def allowed_languages() -> list[str]:
    return get_reference()["languages"]


def artwork_specs() -> dict:
    return get_reference()["artwork_specs"]


def trailer_season() -> int:
    # reference.json describes this convention in prose ("season_zero": "Season 0
    # is reserved for trailers") rather than as a number, since it's a fixed
    # platform convention, not configurable data. We encode the number here.
    return 0
