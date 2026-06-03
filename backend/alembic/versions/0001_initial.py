"""initial schema"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "channels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_channels_username", "channels", ["username"], unique=True)

    op.create_table(
        "collection_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("default_posts_limit", sa.Integer(), nullable=False),
        sa.Column("schedule_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("schedule_hour_utc", sa.Integer(), nullable=False),
        sa.Column("last_collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("post_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("views", sa.Integer(), nullable=False),
        sa.Column("forwards", sa.Integer(), nullable=False),
        sa.Column("reactions_count", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("telegram_message_id", "channel_id", name="uq_posts_message_channel"),
    )
    op.create_index("ix_posts_channel_id", "posts", ["channel_id"], unique=False)
    op.create_index("ix_posts_post_date", "posts", ["post_date"], unique=False)

    op.create_table(
        "entities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_text", sa.String(length=255), nullable=False),
        sa.Column("normalized_text", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_entities_post_id", "entities", ["post_id"], unique=False)
    op.create_index("ix_entities_normalized_text", "entities", ["normalized_text"], unique=False)

    op.create_table(
        "daily_entity_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("entity", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("mentions_count", sa.Integer(), nullable=False),
        sa.Column("channels_count", sa.Integer(), nullable=False),
        sa.Column("total_views", sa.Integer(), nullable=False),
        sa.Column("total_reactions", sa.Integer(), nullable=False),
        sa.Column("growth_7d", sa.Float(), nullable=True),
        sa.Column("growth_30d", sa.Float(), nullable=True),
        sa.Column("trend_score", sa.Float(), nullable=False),
        sa.Column("new_trend", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("date", "entity", "entity_type", name="uq_daily_entity_stats_date_entity_type"),
    )
    op.create_index("ix_daily_entity_stats_date", "daily_entity_stats", ["date"], unique=False)
    op.create_index("ix_daily_entity_stats_entity", "daily_entity_stats", ["entity"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_daily_entity_stats_entity", table_name="daily_entity_stats")
    op.drop_index("ix_daily_entity_stats_date", table_name="daily_entity_stats")
    op.drop_table("daily_entity_stats")
    op.drop_index("ix_entities_normalized_text", table_name="entities")
    op.drop_index("ix_entities_post_id", table_name="entities")
    op.drop_table("entities")
    op.drop_index("ix_posts_post_date", table_name="posts")
    op.drop_index("ix_posts_channel_id", table_name="posts")
    op.drop_table("posts")
    op.drop_table("collection_settings")
    op.drop_index("ix_channels_username", table_name="channels")
    op.drop_table("channels")

