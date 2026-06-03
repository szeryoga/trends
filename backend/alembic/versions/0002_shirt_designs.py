"""shirt designs"""

from alembic import op
import sqlalchemy as sa


revision = "0002_shirt_designs"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shirt_designs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trend_entity", sa.String(length=255), nullable=False),
        sa.Column("trend_entity_type", sa.String(length=120), nullable=False),
        sa.Column("trend_score", sa.Float(), nullable=False),
        sa.Column("trend_growth_7d", sa.Float(), nullable=True),
        sa.Column("brief_prompt", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("image_s3_key", sa.String(length=500), nullable=False),
        sa.Column("image_url", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_shirt_designs_trend_entity", "shirt_designs", ["trend_entity"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_shirt_designs_trend_entity", table_name="shirt_designs")
    op.drop_table("shirt_designs")
