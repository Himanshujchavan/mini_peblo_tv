"""initial schema: users, shows, seasons, episodes, artworks, publish_runs

Revision ID: 0001
Revises:
Create Date: 2026-08-31
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

role_enum = postgresql.ENUM("editor", "admin", name="role")
status_enum = postgresql.ENUM("draft", "published", name="status")
artwork_kind_enum = postgresql.ENUM("poster", "banner", "thumbnail", name="artworkkind")


def upgrade():
    bind = op.get_bind()

    # Manually check and create enum types to avoid DuplicateObject errors
    for enum_name, values in [
        ("role", ["editor", "admin"]),
        ("status", ["draft", "published"]),
        ("artworkkind", ["poster", "banner", "thumbnail"]),
    ]:
        # Check if the type already exists in pg_type
        res = bind.execute(sa.text(f"SELECT 1 FROM pg_type WHERE typname='{enum_name}'")).fetchone()
        if not res:
            bind.execute(sa.text(f"CREATE TYPE {enum_name} AS ENUM ({', '.join([f"'{v}'" for v in values])})"))

    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "shows",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("synopsis", sa.Text(), nullable=True),
        sa.Column("categories", sa.JSON(), nullable=False),
        sa.Column("section", sa.String(), nullable=True),
        sa.Column("status", status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_shows_title", "shows", ["title"])
    op.create_index("ix_shows_section", "shows", ["section"])
    op.create_index("ix_shows_status", "shows", ["status"])
    op.create_index("ix_shows_status_section", "shows", ["status", "section"])

    op.create_table(
        "seasons",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("show_id", sa.String(), sa.ForeignKey("shows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.UniqueConstraint("show_id", "number", name="uq_season_show_number"),
    )

    op.create_table(
        "episodes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("season_id", sa.String(), sa.ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("content_group", sa.String(), nullable=True),
        sa.Column("status", status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("content_group", "language", name="uq_contentgroup_language"),
    )
    op.create_index("ix_episodes_content_group", "episodes", ["content_group"])
    op.create_index("ix_episodes_status", "episodes", ["status"])

    op.create_table(
        "artworks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("show_id", sa.String(), sa.ForeignKey("shows.id", ondelete="CASCADE"), nullable=True),
        sa.Column("episode_id", sa.String(), sa.ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("kind", artwork_kind_enum, nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("show_id", "episode_id", "kind", name="uq_artwork_owner_kind"),
    )

    op.create_table(
        "publish_runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("triggered_by", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("outcome", sa.String(), nullable=False),
        sa.Column("show_count", sa.Integer(), nullable=True),
        sa.Column("episode_count", sa.Integer(), nullable=True),
        sa.Column("catalogue_storage_key", sa.String(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("checksum", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_table("publish_runs")
    op.drop_table("artworks")
    op.drop_table("episodes")
    op.drop_table("seasons")
    op.drop_table("shows")
    op.drop_table("users")
    bind = op.get_bind()
    artwork_kind_enum.drop(bind, checkfirst=True)
    status_enum.drop(bind, checkfirst=True)
    role_enum.drop(bind, checkfirst=True)
