from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.models import PipelineStage, PipelineStatus


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CompanyWrite(BaseModel):
    company_name: str = Field(min_length=2, max_length=200)
    siren: str | None = Field(default=None, pattern=r"^\d{9}$")
    siret: str | None = Field(default=None, pattern=r"^\d{14}$")
    website: HttpUrl | None = None
    description: str | None = None
    employee_count: int | None = Field(default=None, ge=0)
    annual_revenue: Decimal | None = Field(default=None, ge=0)
    headquarters_city: str | None = None
    headquarters_region: str | None = None
    headquarters_country: str = "FR"
    operating_regions: list[str] = []
    service_categories: list[str] = []
    technologies: list[str] = []
    certifications: list[str] = []
    preferred_contract_min: Decimal | None = Field(default=None, ge=0)
    preferred_contract_max: Decimal | None = Field(default=None, ge=0)
    preferred_geographies: list[str] = []
    preferred_buyer_types: list[str] = []
    preferred_categories: list[str] = []
    excluded_categories: list[str] = []

    @model_validator(mode="after")
    def validate_contract_range(self) -> "CompanyWrite":
        if (
            self.preferred_contract_min is not None
            and self.preferred_contract_max is not None
            and self.preferred_contract_min > self.preferred_contract_max
        ):
            raise ValueError("preferred_contract_min cannot exceed preferred_contract_max")
        return self


class CompanyRead(CompanyWrite, ApiModel):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime


class BuyerRead(ApiModel):
    id: str
    source: str
    external_id: str
    name: str
    buyer_type: str | None
    description: str | None
    city: str | None
    region: str | None
    country: str
    website: str | None


class MatchRead(ApiModel):
    total_score: int
    technical_score: int
    geography_score: int
    value_score: int
    sector_score: int
    buyer_score: int
    eligibility_score: int
    positive_reasons: list[str]
    risk_reasons: list[str]
    missing_requirements: list[str]
    scoring_version: str
    calculated_at: datetime
    priority: str


class OpportunityRead(ApiModel):
    id: str
    source: str
    external_id: str
    title: str
    description: str | None
    publication_date: date | None
    deadline: date | None
    estimated_value_min: Decimal | None
    estimated_value_max: Decimal | None
    currency: str
    cpv_codes: list[str]
    categories: list[str]
    technologies: list[str]
    certifications_required: list[str]
    location: str | None
    region: str | None
    country: str
    contract_duration_months: int | None
    procedure_type: str | None
    source_url: str | None
    status: PipelineStatus
    is_demo: bool
    buyer: BuyerRead
    match: MatchRead | None


class OpportunityPage(BaseModel):
    items: list[OpportunityRead]
    total: int
    page: int
    page_size: int


class DashboardSummary(BaseModel):
    total_matched_pipeline: Decimal
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    active_opportunities: int
    average_match_score: float
    closing_in_7_days: int
    closing_in_30_days: int
    largest_opportunity: Decimal | None
    nearest_deadline_days: int | None


class BuyerIntelligence(BuyerRead):
    opportunity_count: int
    active_opportunities: int
    combined_visible_value: Decimal
    categories_observed: list[str]


class StatusUpdate(BaseModel):
    status: PipelineStatus


class RecalculationResult(BaseModel):
    recalculated: int
    scoring_version: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class PipelineItemWrite(BaseModel):
    opportunity_id: str
    stage: PipelineStage = PipelineStage.review
    value: Decimal | None = Field(default=None, ge=0)
    probability: int | None = Field(default=None, ge=0, le=100)
    next_action: str | None = Field(default=None, max_length=500)
    next_action_date: date | None = None
    notes: str | None = Field(default=None, max_length=5000)


class PipelineItemUpdate(BaseModel):
    stage: PipelineStage | None = None
    value: Decimal | None = Field(default=None, ge=0)
    probability: int | None = Field(default=None, ge=0, le=100)
    next_action: str | None = Field(default=None, max_length=500)
    next_action_date: date | None = None
    notes: str | None = Field(default=None, max_length=5000)


class PipelineItemRead(ApiModel):
    id: str
    organization_id: str
    opportunity_id: str
    stage: PipelineStage
    value: Decimal | None
    probability: int | None
    next_action: str | None
    next_action_date: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    opportunity: OpportunityRead


class PipelineSummary(BaseModel):
    total_value: Decimal
    weighted_value: Decimal
    item_count: int
    by_stage: dict[str, int]


class SavedSearchWrite(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    filters: dict[str, str | int | float | bool] = Field(default_factory=dict)
    alerts_enabled: bool = False


class SavedSearchRead(SavedSearchWrite, ApiModel):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime


class NotificationRead(ApiModel):
    id: str
    type: str
    severity: str
    title: str
    message: str
    entity_type: str | None
    entity_id: str | None
    read_at: datetime | None
    created_at: datetime


class ActivityEventRead(ApiModel):
    id: str
    action: str
    entity_type: str
    entity_id: str
    event_metadata: dict[str, Any]
    created_at: datetime


class QualificationRead(BaseModel):
    decision: str
    reasons: list[str]
    blockers: list[str]
    version: str
