"""add pipeline, saved searches, notifications and activity events"""

import sqlalchemy as sa
from alembic import op

revision = "20260814_0002"
down_revision = "20260814_0001"


def upgrade() -> None:
    pipeline_stage = sa.Enum(
        "discovered",
        "review",
        "qualified",
        "bid_decision",
        "preparing",
        "submitted",
        "won",
        "lost",
        "ignored",
        name="pipelinestage",
    )
    op.create_table(
        "pipeline_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column(
            "opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=False
        ),
        sa.Column("stage", pipeline_stage, nullable=False),
        sa.Column("owner_id", sa.String(36)),
        sa.Column("value", sa.Numeric(16, 2)),
        sa.Column("probability", sa.Integer()),
        sa.Column("next_action", sa.String(500)),
        sa.Column("next_action_date", sa.Date()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "organization_id", "opportunity_id", name="uq_pipeline_org_opportunity"
        ),
    )
    op.create_index("ix_pipeline_items_organization_id", "pipeline_items", ["organization_id"])
    op.create_index("ix_pipeline_items_opportunity_id", "pipeline_items", ["opportunity_id"])
    op.create_index("ix_pipeline_org_stage", "pipeline_items", ["organization_id", "stage"])
    op.create_index("ix_pipeline_next_action_date", "pipeline_items", ["next_action_date"])
    op.create_table(
        "saved_searches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("alerts_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "name", name="uq_saved_search_org_name"),
    )
    op.create_index("ix_saved_searches_organization_id", "saved_searches", ["organization_id"])
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column("user_id", sa.String(36)),
        sa.Column("type", sa.String(80), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.String(80)),
        sa.Column("entity_id", sa.String(36)),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notifications_organization_id", "notifications", ["organization_id"])
    op.create_index("ix_notification_org_read", "notifications", ["organization_id", "read_at"])
    op.create_table(
        "activity_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column("actor_id", sa.String(36)),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_activity_events_organization_id", "activity_events", ["organization_id"])
    op.create_index("ix_activity_org_created", "activity_events", ["organization_id", "created_at"])


def downgrade() -> None:
    op.drop_table("activity_events")
    op.drop_table("notifications")
    op.drop_table("saved_searches")
    op.drop_table("pipeline_items")
    if op.get_bind().dialect.name == "postgresql":
        sa.Enum(name="pipelinestage").drop(op.get_bind(), checkfirst=True)
