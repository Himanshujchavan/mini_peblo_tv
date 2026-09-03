import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, ForeignKey, DateTime, Enum, UniqueConstraint,
    Index, Text, JSON
)
from sqlalchemy.orm import relationship

from app.database import Base

# Plain String(36) rather than the Postgres-only UUID type: keeps the schema
# portable (sqlite for fast unit tests, Postgres in docker-compose/prod)
# without needing a TypeDecorator just for this exercise.
UUID = lambda as_uuid=False: String(36)  # noqa: E731


def gen_uuid():
    return str(uuid.uuid4())


class Role(str, enum.Enum):
    editor = "editor"
    admin = "admin"


class Status(str, enum.Enum):
    draft = "draft"
    published = "published"


class ArtworkKind(str, enum.Enum):
    poster = "poster"
    banner = "banner"
    thumbnail = "thumbnail"


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.editor)
    created_at = Column(DateTime, default=datetime.utcnow)


class Show(Base):
    __tablename__ = "shows"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    title = Column(String, nullable=False, index=True)
    synopsis = Column(Text, default="")
    categories = Column(JSON, nullable=False, default=list)  # a show can have several, per reference.json data
    section = Column(String, nullable=True, index=True)  # required at publish time, not at creation
    status = Column(Enum(Status), nullable=False, default=Status.draft, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    seasons = relationship("Season", back_populates="show", cascade="all, delete-orphan")
    artworks = relationship("Artwork", back_populates="show",
                             primaryjoin="and_(Artwork.show_id==Show.id, Artwork.episode_id==None)")

    __table_args__ = (Index("ix_shows_status_section", "status", "section"),)


class Season(Base):
    __tablename__ = "seasons"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    show_id = Column(UUID(as_uuid=False), ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)
    number = Column(Integer, nullable=False)  # 0 == trailers, per reference.json convention

    show = relationship("Show", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("show_id", "number", name="uq_season_show_number"),)


class Episode(Base):
    __tablename__ = "episodes"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    season_id = Column(UUID(as_uuid=False), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    episode_number = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    language = Column(String, nullable=False)  # ISO code, validated against reference.json at write time
    content_group = Column(String, nullable=True, index=True)  # NULL => not part of a language group
    status = Column(Enum(Status), nullable=False, default=Status.draft, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    season = relationship("Season", back_populates="episodes")
    artworks = relationship("Artwork", back_populates="episode")

    __table_args__ = (
        # the core "language variant" invariant from the brief
        UniqueConstraint("content_group", "language", name="uq_contentgroup_language"),
    )


class Artwork(Base):
    """
    Row per (owner, kind). An episode/show can have at most one poster / banner /
    thumbnail at a time — re-upload replaces the file in storage and updates the row,
    it doesn't grow a history (kept simple; audit log is a stretch item).
    """
    __tablename__ = "artworks"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    show_id = Column(UUID(as_uuid=False), ForeignKey("shows.id", ondelete="CASCADE"), nullable=True)
    episode_id = Column(UUID(as_uuid=False), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True)
    kind = Column(Enum(ArtworkKind), nullable=False)
    storage_key = Column(String, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    show = relationship("Show", back_populates="artworks", foreign_keys=[show_id])
    episode = relationship("Episode", back_populates="artworks", foreign_keys=[episode_id])

    __table_args__ = (
        UniqueConstraint("show_id", "episode_id", "kind", name="uq_artwork_owner_kind"),
    )

    @property
    def url(self) -> str:
        from app.storage import get_storage
        return get_storage().url_for(self.storage_key)


class PublishRun(Base):
    __tablename__ = "publish_runs"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    triggered_by = Column(String, nullable=False)  # user email
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    outcome = Column(String, nullable=False, default="running")  # running | success | failed
    show_count = Column(Integer, default=0)
    episode_count = Column(Integer, default=0)
    catalogue_storage_key = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    checksum = Column(String, nullable=True)
