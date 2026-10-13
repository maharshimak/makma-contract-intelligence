"""add identity, memberships, marketplace and tender-to-team foundation"""

import sqlalchemy as sa
from alembic import op

revision = "20260814_0003"
down_revision = "20260814_0002"


def upgrade() -> None:
    for column in [
        sa.Column("organization_type", sa.String(40), nullable=False, server_default="SUPPLIER"),
        sa.Column("siren", sa.String(9)),
        sa.Column("siret", sa.String(14)),
        sa.Column("legal_name", sa.String(240)),
        sa.Column("website", sa.String(500)),
        sa.Column("logo_url", sa.String(1000)),
        sa.Column("description", sa.Text()),
        sa.Column("country", sa.String(2), nullable=False, server_default="FR"),
        sa.Column("region", sa.String(120)),
        sa.Column("city", sa.String(120)),
        sa.Column("employee_count", sa.Integer()),
        sa.Column("annual_revenue", sa.Numeric(16, 2)),
        sa.Column(
            "verification_status", sa.String(30), nullable=False, server_default="UNVERIFIED"
        ),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
    ]:
        op.add_column("organizations", column)

    platform_role = sa.Enum("USER", "ADMIN", "SUPERADMIN", name="platformrole")
    membership_role = sa.Enum(
        "OWNER",
        "ADMIN",
        "SALES_DIRECTOR",
        "BID_MANAGER",
        "PROCUREMENT_ANALYST",
        "TECHNICAL_LEAD",
        "FINANCE",
        "LEGAL",
        "MEMBER",
        "VIEWER",
        name="membershiprole",
    )
    work_post_type = sa.Enum(
        "FULL_TIME_JOB",
        "FREELANCE_ASSIGNMENT",
        "BID_PROJECT",
        "EXPERT_REQUEST",
        "SUBCONTRACTING_REQUEST",
        "CONSORTIUM_PARTNER_REQUEST",
        name="workposttype",
    )
    gap_type = sa.Enum(
        "SKILL",
        "CERTIFICATION",
        "REFERENCE",
        "CAPACITY",
        "GEOGRAPHY",
        "LANGUAGE",
        "SECURITY",
        "ENVIRONMENTAL",
        "FINANCIAL",
        "LEGAL",
        "TECHNOLOGY",
        "EXPERIENCE",
        "EVIDENCE",
        name="gaptype",
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True)),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("avatar_url", sa.String(1000)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("platform_role", platform_role, nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table(
        "auth_identities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("provider_subject", sa.String(320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider", "provider_subject", name="uq_auth_provider_subject"),
    )
    op.create_index("ix_auth_identities_user_id", "auth_identities", ["user_id"])
    op.create_table(
        "professional_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("headline", sa.String(240)),
        sa.Column("bio", sa.Text()),
        sa.Column("location", sa.String(200)),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("preferred_regions", sa.JSON(), nullable=False),
        sa.Column("languages", sa.JSON(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("technologies", sa.JSON(), nullable=False),
        sa.Column("certifications", sa.JSON(), nullable=False),
        sa.Column("industries", sa.JSON(), nullable=False),
        sa.Column("procurement_experience", sa.JSON(), nullable=False),
        sa.Column("years_experience", sa.Integer()),
        sa.Column("availability_status", sa.String(80)),
        sa.Column("available_from", sa.Date()),
        sa.Column("daily_rate", sa.Numeric(12, 2)),
        sa.Column("preferred_engagements", sa.JSON(), nullable=False),
        sa.Column("remote_preference", sa.String(40)),
        sa.Column("visibility", sa.String(30), nullable=False),
        sa.Column("portfolio_items", sa.JSON(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_professional_profiles_user_id", "professional_profiles", ["user_id"])
    op.create_table(
        "organization_members",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", membership_role, nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("invited_by", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("joined_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_member_user"),
    )
    op.create_index(
        "ix_organization_members_organization_id", "organization_members", ["organization_id"]
    )
    op.create_index("ix_organization_members_user_id", "organization_members", ["user_id"])
    op.create_table(
        "capability_gaps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=False
        ),
        sa.Column(
            "organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column("requirement_id", sa.String(36)),
        sa.Column("gap_type", gap_type, nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("capability", sa.String(240), nullable=False),
        sa.Column("mandatory", sa.Boolean(), nullable=False),
        sa.Column("resolution_status", sa.String(30), nullable=False),
        sa.Column("coverage_weight", sa.Integer(), nullable=False),
        sa.Column("provenance", sa.String(30), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "opportunity_id",
            "organization_id",
            "capability",
            name="uq_gap_opportunity_org_capability",
        ),
    )
    op.create_index(
        "ix_gap_org_opportunity", "capability_gaps", ["organization_id", "opportunity_id"]
    )
    op.create_index("ix_capability_gaps_opportunity_id", "capability_gaps", ["opportunity_id"])
    op.create_index("ix_capability_gaps_organization_id", "capability_gaps", ["organization_id"])
    op.create_table(
        "work_posts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id")),
        sa.Column("capability_gap_id", sa.String(36), sa.ForeignKey("capability_gaps.id")),
        sa.Column("post_type", work_post_type, nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("location", sa.String(200)),
        sa.Column("remote_policy", sa.String(40)),
        sa.Column("required_skills", sa.JSON(), nullable=False),
        sa.Column("required_certifications", sa.JSON(), nullable=False),
        sa.Column("compensation_min", sa.Numeric(12, 2)),
        sa.Column("compensation_max", sa.Numeric(12, 2)),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("contingent_on_award", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for name, cols in [
        ("ix_work_post_org_status", ["organization_id", "status"]),
        ("ix_work_posts_organization_id", ["organization_id"]),
        ("ix_work_posts_created_by", ["created_by"]),
        ("ix_work_posts_opportunity_id", ["opportunity_id"]),
        ("ix_work_posts_capability_gap_id", ["capability_gap_id"]),
    ]:
        op.create_index(name, "work_posts", cols)
    op.create_table(
        "applications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("work_post_id", sa.String(36), sa.ForeignKey("work_posts.id"), nullable=False),
        sa.Column(
            "professional_profile_id",
            sa.String(36),
            sa.ForeignKey("professional_profiles.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "work_post_id", "professional_profile_id", name="uq_application_post_professional"
        ),
    )
    op.create_index("ix_applications_work_post_id", "applications", ["work_post_id"])
    op.create_index(
        "ix_applications_professional_profile_id", "applications", ["professional_profile_id"]
    )
    op.create_table(
        "invitations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column(
            "professional_profile_id",
            sa.String(36),
            sa.ForeignKey("professional_profiles.id"),
            nullable=False,
        ),
        sa.Column("work_post_id", sa.String(36), sa.ForeignKey("work_posts.id")),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id")),
        sa.Column("invited_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True)),
    )
    for col in ["organization_id", "professional_profile_id", "work_post_id", "opportunity_id"]:
        op.create_index(f"ix_invitations_{col}", "invitations", [col])
    op.create_table(
        "bid_teams",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column(
            "opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=False
        ),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "organization_id", "opportunity_id", name="uq_bid_team_org_opportunity"
        ),
    )
    op.create_index("ix_bid_teams_organization_id", "bid_teams", ["organization_id"])
    op.create_index("ix_bid_teams_opportunity_id", "bid_teams", ["opportunity_id"])
    op.create_table(
        "bid_team_members",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("bid_team_id", sa.String(36), sa.ForeignKey("bid_teams.id"), nullable=False),
        sa.Column("member_type", sa.String(30), nullable=False),
        sa.Column("member_id", sa.String(36), nullable=False),
        sa.Column("display_name", sa.String(240), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("bid_team_id", "member_type", "member_id", name="uq_bid_team_member"),
    )
    op.create_index("ix_bid_team_members_bid_team_id", "bid_team_members", ["bid_team_id"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id")),
        sa.Column("actor_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("reason", sa.String(500)),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_org_created", "audit_logs", ["organization_id", "created_at"])
    op.create_index("ix_audit_logs_organization_id", "audit_logs", ["organization_id"])
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])


def downgrade() -> None:
    for table in [
        "audit_logs",
        "bid_team_members",
        "bid_teams",
        "invitations",
        "applications",
        "work_posts",
        "capability_gaps",
        "organization_members",
        "professional_profiles",
        "auth_identities",
        "users",
    ]:
        op.drop_table(table)
    for column in [
        "is_demo",
        "verification_status",
        "annual_revenue",
        "employee_count",
        "city",
        "region",
        "country",
        "description",
        "logo_url",
        "website",
        "legal_name",
        "siret",
        "siren",
        "organization_type",
    ]:
        op.drop_column("organizations", column)
    if op.get_bind().dialect.name == "postgresql":
        for name in ["gaptype", "workposttype", "membershiprole", "platformrole"]:
            sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)
