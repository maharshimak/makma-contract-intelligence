"""initial domain schema"""

import sqlalchemy as sa
from alembic import op

revision = "20260814_0001"
down_revision = None


def upgrade() -> None:
    pipeline_status = sa.Enum(
        "discovered",
        "reviewing",
        "qualified",
        "bidding",
        "submitted",
        "won",
        "lost",
        "ignored",
        name="pipelinestatus",
    )
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])
    op.create_table(
        "company_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column("company_name", sa.String(200), nullable=False),
        sa.Column("siren", sa.String(9)),
        sa.Column("siret", sa.String(14)),
        sa.Column("website", sa.String(500)),
        sa.Column("description", sa.Text()),
        sa.Column("employee_count", sa.Integer()),
        sa.Column("annual_revenue", sa.Numeric(16, 2)),
        sa.Column("headquarters_city", sa.String(120)),
        sa.Column("headquarters_region", sa.String(120)),
        sa.Column("headquarters_country", sa.String(2), nullable=False),
        sa.Column("operating_regions", sa.JSON(), nullable=False),
        sa.Column("service_categories", sa.JSON(), nullable=False),
        sa.Column("technologies", sa.JSON(), nullable=False),
        sa.Column("certifications", sa.JSON(), nullable=False),
        sa.Column("preferred_contract_min", sa.Numeric(16, 2)),
        sa.Column("preferred_contract_max", sa.Numeric(16, 2)),
        sa.Column("preferred_geographies", sa.JSON(), nullable=False),
        sa.Column("preferred_buyer_types", sa.JSON(), nullable=False),
        sa.Column("preferred_categories", sa.JSON(), nullable=False),
        sa.Column("excluded_categories", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id"),
    )
    op.create_index("ix_company_profiles_organization_id", "company_profiles", ["organization_id"])
    op.create_table(
        "buyers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("buyer_type", sa.String(100)),
        sa.Column("description", sa.Text()),
        sa.Column("city", sa.String(120)),
        sa.Column("region", sa.String(120)),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("website", sa.String(500)),
        sa.Column("raw_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source", "external_id", name="uq_buyer_source_external"),
    )
    op.create_index("ix_buyers_name", "buyers", ["name"])
    op.create_table(
        "opportunities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("buyer_id", sa.String(36), sa.ForeignKey("buyers.id"), nullable=False),
        sa.Column("publication_date", sa.Date()),
        sa.Column("deadline", sa.Date()),
        sa.Column("estimated_value_min", sa.Numeric(16, 2)),
        sa.Column("estimated_value_max", sa.Numeric(16, 2)),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("cpv_codes", sa.JSON(), nullable=False),
        sa.Column("categories", sa.JSON(), nullable=False),
        sa.Column("technologies", sa.JSON(), nullable=False),
        sa.Column("certifications_required", sa.JSON(), nullable=False),
        sa.Column("location", sa.String(200)),
        sa.Column("region", sa.String(120)),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("contract_duration_months", sa.Integer()),
        sa.Column("procedure_type", sa.String(120)),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("raw_metadata", sa.JSON(), nullable=False),
        sa.Column("status", pipeline_status, nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source", "external_id", name="uq_opportunity_source_external"),
    )
    op.create_index("ix_opportunities_buyer_id", "opportunities", ["buyer_id"])
    op.create_index("ix_opportunity_deadline", "opportunities", ["deadline"])
    op.create_index("ix_opportunity_publication", "opportunities", ["publication_date"])
    op.create_table(
        "opportunity_matches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "company_profile_id",
            sa.String(36),
            sa.ForeignKey("company_profiles.id"),
            nullable=False,
        ),
        sa.Column(
            "opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=False
        ),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("technical_score", sa.Integer(), nullable=False),
        sa.Column("geography_score", sa.Integer(), nullable=False),
        sa.Column("value_score", sa.Integer(), nullable=False),
        sa.Column("sector_score", sa.Integer(), nullable=False),
        sa.Column("buyer_score", sa.Integer(), nullable=False),
        sa.Column("eligibility_score", sa.Integer(), nullable=False),
        sa.Column("positive_reasons", sa.JSON(), nullable=False),
        sa.Column("risk_reasons", sa.JSON(), nullable=False),
        sa.Column("missing_requirements", sa.JSON(), nullable=False),
        sa.Column("scoring_version", sa.String(50), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "company_profile_id", "opportunity_id", name="uq_match_company_opportunity"
        ),
    )
    op.create_index(
        "ix_opportunity_matches_company_profile_id", "opportunity_matches", ["company_profile_id"]
    )
    op.create_index(
        "ix_opportunity_matches_opportunity_id", "opportunity_matches", ["opportunity_id"]
    )
    op.create_index("ix_match_score", "opportunity_matches", ["total_score"])


def downgrade() -> None:
    for table in [
        "opportunity_matches",
        "opportunities",
        "buyers",
        "company_profiles",
        "organizations",
    ]:
        op.drop_table(table)
    if op.get_bind().dialect.name == "postgresql":
        sa.Enum(name="pipelinestatus").drop(op.get_bind(), checkfirst=True)
