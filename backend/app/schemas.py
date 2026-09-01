from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


# ---------- auth ----------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str


# ---------- shows ----------
class ShowCreate(BaseModel):
    title: str
    synopsis: str = ""
    categories: List[str]
    section: Optional[str] = None


class ShowUpdate(BaseModel):
    title: Optional[str] = None
    synopsis: Optional[str] = None
    categories: Optional[List[str]] = None
    section: Optional[str] = None
    status: Optional[str] = None


class ShowOut(BaseModel):
    id: str
    title: str
    synopsis: str
    categories: List[str]
    section: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- seasons ----------
class SeasonCreate(BaseModel):
    number: int = Field(ge=0)


class SeasonOut(BaseModel):
    id: str
    show_id: str
    number: int

    class Config:
        from_attributes = True


# ---------- episodes ----------
class EpisodeCreate(BaseModel):
    title: str
    episode_number: int
    duration_seconds: Optional[int] = None
    language: str
    content_group: Optional[str] = None
    status: str = "draft"


class EpisodeUpdate(BaseModel):
    title: Optional[str] = None
    episode_number: Optional[int] = None
    duration_seconds: Optional[int] = None
    language: Optional[str] = None
    content_group: Optional[str] = None
    status: Optional[str] = None


class ArtworkOut(BaseModel):
    kind: str
    url: str
    width: int
    height: int
    size_bytes: int

    class Config:
        from_attributes = True


class EpisodeOut(BaseModel):
    id: str
    season_id: str
    title: str
    episode_number: int
    duration_seconds: Optional[int]
    language: str
    content_group: Optional[str]
    status: str
    artworks: List[ArtworkOut] = []

    class Config:
        from_attributes = True


# ---------- artwork ----------
class ArtworkUploadResult(BaseModel):
    kind: str
    url: str
    width: int
    height: int
    size_bytes: int


# ---------- validation / publish ----------
class ValidationIssue(BaseModel):
    entity_type: str        # "show" | "episode"
    entity_id: str
    entity_label: str       # human readable, e.g. show title + episode title
    issue: str               # human readable reason
    field: Optional[str] = None


class ValidationGroup(BaseModel):
    rule: str
    count: int
    issues: List[ValidationIssue]


class ValidationReport(BaseModel):
    can_publish: bool
    groups: List[ValidationGroup]


class PublishRunOut(BaseModel):
    id: str
    triggered_by: str
    started_at: datetime
    finished_at: Optional[datetime]
    outcome: str
    show_count: int
    episode_count: int
    error: Optional[str]

    class Config:
        from_attributes = True
