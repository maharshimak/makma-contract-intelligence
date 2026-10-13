import enum
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class PipelineStatus(str, enum.Enum):
    discovered = "discovered"
    reviewing = "reviewing"
    qualified = "qualified"
    bidding = "bidding"
    submitted = "submitted"
    won = "won"
    lost = "lost"
    ignored = "ignored"


class PipelineStage(str, enum.Enum):
    discovered = "discovered"
    review = "review"
    qualified = "qualified"
    bid_decision = "bid_decision"
    preparing = "preparing"
    submitted = "submitted"
    won = "won"
    lost = "lost"
    ignored = "ignored"


class PlatformRole(str, enum.Enum):
    user = "USER"
    admin = "ADMIN"
    superadmin = "SUPERADMIN"


class MembershipRole(str, enum.Enum):
    owner = "OWNER"
    admin = "ADMIN"
    sales_director = "SALES_DIRECTOR"
    bid_manager = "BID_MANAGER"
    procurement_analyst = "PROCUREMENT_ANALYST"
    technical_lead = "TECHNICAL_LEAD"
    finance = "FINANCE"
    legal = "LEGAL"
    member = "MEMBER"
    viewer = "VIEWER"


class WorkPostType(str, enum.Enum):
    full_time_job = "FULL_TIME_JOB"
    freelance_assignment = "FREELANCE_ASSIGNMENT"
    bid_project = "BID_PROJECT"
    expert_request = "EXPERT_REQUEST"
    subcontracting_request = "SUBCONTRACTING_REQUEST"
    consortium_partner_request = "CONSORTIUM_PARTNER_REQUEST"


class GapType(str, enum.Enum):
    skill = "SKILL"
    certification = "CERTIFICATION"
    reference = "REFERENCE"
    capacity = "CAPACITY"
    geography = "GEOGRAPHY"
    language = "LANGUAGE"
    security = "SECURITY"
    environmental = "ENVIRONMENTAL"
    financial = "FINANCIAL"
    legal = "LEGAL"
    technology = "TECHNOLOGY"
    experience = "EXPERIENCE"
    evidence = "EVIDENCE"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email"), Index("ix_users_email", "email"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(320))
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    display_name: Mapped[str] = mapped_column(String(200))
    avatar_url: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    platform_role: Mapped[PlatformRole] = mapped_column(
        Enum(PlatformRole), default=PlatformRole.user
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuthIdentity(Base):
    __tablename__ = "auth_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_subject", name="uq_auth_provider_subject"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String(40))
    provider_subject: Mapped[str] = mapped_column(String(320))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class PasswordCredential(Base):
    __tablename__ = "password_credentials"
    __table_args__ = (
        UniqueConstraint("auth_identity_id", name="uq_password_credential_identity"),
        Index("ix_password_credentials_auth_identity_id", "auth_identity_id", unique=True),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    auth_identity_id: Mapped[str] = mapped_column(
        ForeignKey("auth_identities.id", ondelete="CASCADE")
    )
    password_hash: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_user_session_token_hash"),
        Index("ix_user_sessions_token_hash", "token_hash", unique=True),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64))
    csrf_token_hash: Mapped[str] = mapped_column(String(64))
    active_workspace_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProfessionalProfile(Base):
    __tablename__ = "professional_profiles"
    __table_args__ = (
        UniqueConstraint("user_id"),
        Index("ix_professional_profiles_user_id", "user_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    headline: Mapped[str | None] = mapped_column(String(240))
    bio: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(200))
    country: Mapped[str] = mapped_column(String(2), default="FR")
    preferred_regions: Mapped[list[str]] = mapped_column(JSON, default=list)
    languages: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    technologies: Mapped[list[str]] = mapped_column(JSON, default=list)
    certifications: Mapped[list[str]] = mapped_column(JSON, default=list)
    industries: Mapped[list[str]] = mapped_column(JSON, default=list)
    procurement_experience: Mapped[list[str]] = mapped_column(JSON, default=list)
    years_experience: Mapped[int | None] = mapped_column(Integer)
    availability_status: Mapped[str | None] = mapped_column(String(80))
    available_from: Mapped[date | None] = mapped_column(Date)
    daily_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    preferred_engagements: Mapped[list[str]] = mapped_column(JSON, default=list)
    remote_preference: Mapped[str | None] = mapped_column(String(40))
    visibility: Mapped[str] = mapped_column(String(30), default="NETWORK")
    portfolio_items: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    organization_type: Mapped[str] = mapped_column(String(40), default="SUPPLIER")
    siren: Mapped[str | None] = mapped_column(String(9))
    siret: Mapped[str | None] = mapped_column(String(14))
    legal_name: Mapped[str | None] = mapped_column(String(240))
    website: Mapped[str | None] = mapped_column(String(500))
    logo_url: Mapped[str | None] = mapped_column(String(1000))
    description: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str] = mapped_column(String(2), default="FR")
    region: Mapped[str | None] = mapped_column(String(120))
    city: Mapped[str | None] = mapped_column(String(120))
    employee_count: Mapped[int | None] = mapped_column(Integer)
    annual_revenue: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    verification_status: Mapped[str] = mapped_column(String(30), default="UNVERIFIED")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class OrganizationMember(Base):
    __tablename__ = "organization_members"
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_org_member_user"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[MembershipRole] = mapped_column(
        Enum(MembershipRole), default=MembershipRole.member
    )
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    invited_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=utcnow)


class CompanyProfile(Base):
    __tablename__ = "company_profiles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id"), unique=True, index=True
    )
    company_name: Mapped[str] = mapped_column(String(200))
    siren: Mapped[str | None] = mapped_column(String(9))
    siret: Mapped[str | None] = mapped_column(String(14))
    website: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    employee_count: Mapped[int | None] = mapped_column(Integer)
    annual_revenue: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    headquarters_city: Mapped[str | None] = mapped_column(String(120))
    headquarters_region: Mapped[str | None] = mapped_column(String(120))
    headquarters_country: Mapped[str] = mapped_column(String(2), default="FR")
    operating_regions: Mapped[list[str]] = mapped_column(JSON, default=list)
    service_categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    technologies: Mapped[list[str]] = mapped_column(JSON, default=list)
    certifications: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_contract_min: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    preferred_contract_max: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    preferred_geographies: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_buyer_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    excluded_categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Buyer(Base):
    __tablename__ = "buyers"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_buyer_source_external"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(30))
    external_id: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(300), index=True)
    buyer_type: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str] = mapped_column(String(2), default="FR")
    website: Mapped[str | None] = mapped_column(String(500))
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    opportunities: Mapped[list["Opportunity"]] = relationship(back_populates="buyer")


class Opportunity(Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_opportunity_source_external"),
        Index("ix_opportunity_deadline", "deadline"),
        Index("ix_opportunity_publication", "publication_date"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(30))
    external_id: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("buyers.id"), index=True)
    publication_date: Mapped[date | None] = mapped_column(Date)
    deadline: Mapped[date | None] = mapped_column(Date)
    estimated_value_min: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    estimated_value_max: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    cpv_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    technologies: Mapped[list[str]] = mapped_column(JSON, default=list)
    certifications_required: Mapped[list[str]] = mapped_column(JSON, default=list)
    location: Mapped[str | None] = mapped_column(String(200))
    region: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str] = mapped_column(String(2), default="FR")
    contract_duration_months: Mapped[int | None] = mapped_column(Integer)
    procedure_type: Mapped[str | None] = mapped_column(String(120))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    data_classification: Mapped[str] = mapped_column(String(30), default="SOURCE_DERIVED")
    source_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    normalization_version: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus), default=PipelineStatus.discovered
    )
    is_demo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    buyer: Mapped[Buyer] = relationship(back_populates="opportunities")
    matches: Mapped[list["OpportunityMatch"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )


class RawProcurementRecord(Base):
    __tablename__ = "raw_procurement_records"
    __table_args__ = (
        UniqueConstraint("source", "external_id", "payload_hash", name="uq_raw_source_record_hash"),
        Index("ix_raw_source_ingested", "source", "ingested_at"),
        Index("ix_raw_processing_status", "processing_status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(30))
    external_id: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    payload_hash: Mapped[str] = mapped_column(String(64))
    source_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    normalization_version: Mapped[str] = mapped_column(String(50))
    processing_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    quality_status: Mapped[str] = mapped_column(String(30), default="UNCHECKED")
    quality_issues: Mapped[list[str]] = mapped_column(JSON, default=list)
    opportunity_id: Mapped[str | None] = mapped_column(ForeignKey("opportunities.id"), index=True)


class ProcurementIngestionRun(Base):
    __tablename__ = "procurement_ingestion_runs"
    __table_args__ = (Index("ix_ingestion_source_started", "source", "started_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="RUNNING")
    requested_limit: Mapped[int] = mapped_column(Integer)
    fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    unchanged_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OpportunityMatch(Base):
    __tablename__ = "opportunity_matches"
    __table_args__ = (
        UniqueConstraint(
            "company_profile_id", "opportunity_id", name="uq_match_company_opportunity"
        ),
        Index("ix_match_score", "total_score"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_profile_id: Mapped[str] = mapped_column(ForeignKey("company_profiles.id"), index=True)
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id"), index=True)
    total_score: Mapped[int] = mapped_column(Integer)
    technical_score: Mapped[int] = mapped_column(Integer)
    geography_score: Mapped[int] = mapped_column(Integer)
    value_score: Mapped[int] = mapped_column(Integer)
    sector_score: Mapped[int] = mapped_column(Integer)
    buyer_score: Mapped[int] = mapped_column(Integer)
    eligibility_score: Mapped[int] = mapped_column(Integer)
    positive_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    risk_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_requirements: Mapped[list[str]] = mapped_column(JSON, default=list)
    scoring_version: Mapped[str] = mapped_column(String(50))
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    opportunity: Mapped[Opportunity] = relationship(back_populates="matches")


class PipelineItem(Base):
    __tablename__ = "pipeline_items"
    __table_args__ = (
        UniqueConstraint("organization_id", "opportunity_id", name="uq_pipeline_org_opportunity"),
        Index("ix_pipeline_org_stage", "organization_id", "stage"),
        Index("ix_pipeline_next_action_date", "next_action_date"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id"), index=True)
    stage: Mapped[PipelineStage] = mapped_column(Enum(PipelineStage), default=PipelineStage.review)
    owner_id: Mapped[str | None] = mapped_column(String(36))
    value: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    probability: Mapped[int | None] = mapped_column(Integer)
    next_action: Mapped[str | None] = mapped_column(String(500))
    next_action_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    opportunity: Mapped[Opportunity] = relationship()


class SavedSearch(Base):
    __tablename__ = "saved_searches"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_saved_search_org_name"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    filters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    alerts_enabled: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notification_org_read", "organization_id", "read_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(20), default="info")
    title: Mapped[str] = mapped_column(String(240))
    message: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[str | None] = mapped_column(String(80))
    entity_id: Mapped[str | None] = mapped_column(String(36))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ActivityEvent(Base):
    __tablename__ = "activity_events"
    __table_args__ = (Index("ix_activity_org_created", "organization_id", "created_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    actor_id: Mapped[str | None] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(36))
    event_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkPost(Base):
    __tablename__ = "work_posts"
    __table_args__ = (Index("ix_work_post_org_status", "organization_id", "status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    opportunity_id: Mapped[str | None] = mapped_column(ForeignKey("opportunities.id"), index=True)
    capability_gap_id: Mapped[str | None] = mapped_column(
        ForeignKey("capability_gaps.id"), index=True
    )
    post_type: Mapped[WorkPostType] = mapped_column(Enum(WorkPostType))
    title: Mapped[str] = mapped_column(String(240))
    summary: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(200))
    remote_policy: Mapped[str | None] = mapped_column(String(40))
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    required_certifications: Mapped[list[str]] = mapped_column(JSON, default=list)
    compensation_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    compensation_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    contingent_on_award: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(30), default="OPEN")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint(
            "work_post_id", "professional_profile_id", name="uq_application_post_professional"
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    work_post_id: Mapped[str] = mapped_column(ForeignKey("work_posts.id"), index=True)
    professional_profile_id: Mapped[str] = mapped_column(
        ForeignKey("professional_profiles.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED")
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Invitation(Base):
    __tablename__ = "invitations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    professional_profile_id: Mapped[str] = mapped_column(
        ForeignKey("professional_profiles.id"), index=True
    )
    work_post_id: Mapped[str | None] = mapped_column(ForeignKey("work_posts.id"), index=True)
    opportunity_id: Mapped[str | None] = mapped_column(ForeignKey("opportunities.id"), index=True)
    invited_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CapabilityGap(Base):
    __tablename__ = "capability_gaps"
    __table_args__ = (
        UniqueConstraint(
            "opportunity_id",
            "organization_id",
            "capability",
            name="uq_gap_opportunity_org_capability",
        ),
        Index("ix_gap_org_opportunity", "organization_id", "opportunity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id"), index=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    requirement_id: Mapped[str | None] = mapped_column(String(36))
    gap_type: Mapped[GapType] = mapped_column(Enum(GapType))
    severity: Mapped[str] = mapped_column(String(30))
    capability: Mapped[str] = mapped_column(String(240))
    mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_status: Mapped[str] = mapped_column(String(30), default="OPEN")
    coverage_weight: Mapped[int] = mapped_column(Integer, default=5)
    provenance: Mapped[str] = mapped_column(String(30), default="SOURCE_DERIVED")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BidTeam(Base):
    __tablename__ = "bid_teams"
    __table_args__ = (
        UniqueConstraint("organization_id", "opportunity_id", name="uq_bid_team_org_opportunity"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id"), index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(30), default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class BidTeamMember(Base):
    __tablename__ = "bid_team_members"
    __table_args__ = (
        UniqueConstraint("bid_team_id", "member_type", "member_id", name="uq_bid_team_member"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bid_team_id: Mapped[str] = mapped_column(ForeignKey("bid_teams.id"), index=True)
    member_type: Mapped[str] = mapped_column(String(30))
    member_id: Mapped[str] = mapped_column(String(36))
    display_name: Mapped[str] = mapped_column(String(240))
    capabilities: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="PROPOSED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_org_created", "organization_id", "created_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id"), index=True)
    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(36))
    reason: Mapped[str | None] = mapped_column(String(500))
    audit_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
