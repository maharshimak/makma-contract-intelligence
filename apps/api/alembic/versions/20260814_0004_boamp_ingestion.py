"""add raw procurement ingestion and opportunity provenance"""

import sqlalchemy as sa
from alembic import op

revision = "20260814_0004"
down_revision = "20260814_0003"


def upgrade() -> None:
    op.add_column(
        "opportunities",
        sa.Column(
            "data_classification",
            sa.String(30),
            nullable=False,
            server_default="SOURCE_DERIVED",
        ),
    )
    op.add_column("opportunities", sa.Column("source_published_at", sa.DateTime(timezone=True)))
    op.add_column("opportunities", sa.Column("source_updated_at", sa.DateTime(timezone=True)))
    op.add_column("opportunities", sa.Column("ingested_at", sa.DateTime(timezone=True)))
    op.add_column("opportunities", sa.Column("normalization_version", sa.String(50)))

    op.create_table(
        "procurement_ingestion_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("requested_limit", sa.Integer(), nullable=False),
        sa.Column("fetched_count", sa.Integer(), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False),
        sa.Column("updated_count", sa.Integer(), nullable=False),
        sa.Column("unchanged_count", sa.Integer(), nullable=False),
        sa.Column("rejected_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_ingestion_source_started", "procurement_ingestion_runs", ["source", "started_at"]
    )
    op.create_table(
        "raw_procurement_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("source_published_at", sa.DateTime(timezone=True)),
        sa.Column("source_updated_at", sa.DateTime(timezone=True)),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("normalization_version", sa.String(50), nullable=False),
        sa.Column("processing_status", sa.String(30), nullable=False),
        sa.Column("quality_status", sa.String(30), nullable=False),
        sa.Column("quality_issues", sa.JSON(), nullable=False),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id")),
        sa.UniqueConstraint(
            "source", "external_id", "payload_hash", name="uq_raw_source_record_hash"
        ),
    )
    op.create_index(
        "ix_raw_source_ingested", "raw_procurement_records", ["source", "ingested_at"]
    )
    op.create_index(
        "ix_raw_processing_status", "raw_procurement_records", ["processing_status"]
    )
    op.create_index(
        "ix_raw_procurement_records_opportunity_id",
        "raw_procurement_records",
        ["opportunity_id"],
    )


def downgrade() -> None:
    op.drop_table("raw_procurement_records")
    op.drop_table("procurement_ingestion_runs")
    for column in [
        "normalization_version",
        "ingested_at",
        "source_updated_at",
        "source_published_at",
        "data_classification",
    ]:
        op.drop_column("opportunities", column)
