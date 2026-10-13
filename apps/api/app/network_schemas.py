from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models import GapType, MembershipRole, PlatformRole, WorkPostType


class WorkspaceRead(BaseModel):
    id: str
    name: str
    slug: str
    role: MembershipRole
    organization_type: str
    is_demo: bool


class SessionRead(BaseModel):
    user_id: str
    email: str
    display_name: str
    platform_role: PlatformRole
    active_workspace: WorkspaceRead | None
    workspaces: list[WorkspaceRead]
    has_professional_profile: bool
    company_profile_complete: bool
    onboarding_required: bool
    demo_session: bool = False


class ProfessionalRead(BaseModel):
    id: str
    user_id: str
    display_name: str
    headline: str | None
    bio: str | None
    location: str | None
    country: str
    skills: list[str]
    technologies: list[str]
    certifications: list[str]
    industries: list[str]
    procurement_experience: list[str]
    years_experience: int | None
    availability_status: str | None
    daily_rate: Decimal | None
    preferred_engagements: list[str]
    remote_preference: str | None
    profile_strength: int
    is_demo: bool


class WorkPostWrite(BaseModel):
    post_type: WorkPostType
    title: str = Field(min_length=4, max_length=240)
    summary: str = Field(min_length=20, max_length=5000)
    opportunity_id: str | None = None
    capability_gap_id: str | None = None
    location: str | None = None
    remote_policy: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    required_certifications: list[str] = Field(default_factory=list)
    compensation_min: Decimal | None = Field(default=None, ge=0)
    compensation_max: Decimal | None = Field(default=None, ge=0)
    contingent_on_award: bool = False

    @model_validator(mode="after")
    def validate_compensation(self) -> "WorkPostWrite":
        if (
            self.compensation_min is not None
            and self.compensation_max is not None
            and self.compensation_min > self.compensation_max
        ):
            raise ValueError("compensation_min cannot exceed compensation_max")
        if self.opportunity_id and not self.contingent_on_award:
            raise ValueError("tender-linked work must be marked contingent_on_award")
        return self


class WorkPostRead(BaseModel):
    id: str
    organization_id: str
    organization_name: str
    post_type: WorkPostType
    title: str
    summary: str
    opportunity_id: str | None
    opportunity_title: str | None
    location: str | None
    remote_policy: str | None
    required_skills: list[str]
    required_certifications: list[str]
    compensation_min: Decimal | None
    compensation_max: Decimal | None
    currency: str
    contingent_on_award: bool
    status: str
    is_demo: bool
    match_reasons: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    created_at: datetime


class ApplicationWrite(BaseModel):
    note: str | None = Field(default=None, max_length=3000)


class ApplicationRead(BaseModel):
    id: str
    work_post_id: str
    work_post_title: str
    professional_profile_id: str
    professional_name: str
    status: str
    note: str | None
    created_at: datetime


class CapabilityGapRead(BaseModel):
    id: str
    gap_type: GapType
    severity: str
    capability: str
    mandatory: bool
    resolution_status: str
    coverage_weight: int
    provenance: str
    is_demo: bool


class TeamCandidateRead(BaseModel):
    candidate_type: str
    candidate_id: str
    name: str
    headline: str | None
    suitability: int
    capabilities: list[str]
    resolves_gap_ids: list[str]
    is_demo: bool


class TeamRecommendationRead(BaseModel):
    current_coverage: int
    candidates: list[TeamCandidateRead]


class TeamMemberSelection(BaseModel):
    candidate_type: str
    candidate_id: str


class BidTeamWrite(BaseModel):
    name: str = Field(min_length=3, max_length=240)
    members: list[TeamMemberSelection]


class BidTeamRead(BaseModel):
    id: str
    opportunity_id: str
    name: str
    status: str
    current_coverage: int
    proposed_coverage: int
    members: list[TeamCandidateRead]
    created_at: datetime


class AdminSummaryRead(BaseModel):
    users: int
    organizations: int
    professionals: int
    procurement_records: int
    open_work_posts: int
    demo_only: bool
