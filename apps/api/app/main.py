import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import String, func, select
from sqlalchemy.orm import Session, joinedload

from app.auth import Principal, current_principal, require_manager
from app.auth_routes import router as auth_router
from app.config import get_settings
from app.database import engine, get_db
from app.models import (
    ActivityEvent,
    Buyer,
    CompanyProfile,
    MembershipRole,
    Notification,
    Opportunity,
    OpportunityMatch,
    Organization,
    OrganizationMember,
    PipelineStatus,
    SavedSearch,
)
from app.network_routes import router as network_router
from app.procurement_routes import router as procurement_router
from app.qualification import qualify_opportunity
from app.schemas import (
    ActivityEventRead,
    BuyerIntelligence,
    CompanyRead,
    CompanyWrite,
    DashboardSummary,
    NotificationRead,
    OpportunityPage,
    OpportunityRead,
    PipelineItemRead,
    PipelineItemUpdate,
    PipelineItemWrite,
    PipelineSummary,
    QualificationRead,
    RecalculationResult,
    SavedSearchRead,
    SavedSearchWrite,
    StatusUpdate,
)
from app.scoring import SCORING_VERSION
from app.services import (
    dashboard_metrics,
    opportunity_value,
    recalculate_matches,
    serialize_opportunity,
)
from app.workflow import (
    add_pipeline_item,
    create_saved_search,
    pipeline_items,
    pipeline_summary,
    serialize_pipeline_item,
    update_pipeline_item,
)

settings = get_settings()
logging.basicConfig(
    level=settings.log_level,
    format='{"level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger("contract_os")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate_runtime_safety()
    with engine.connect():
        logger.info("database_connection_ready")
    logger.info("application_started")
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(network_router)
app.include_router(procurement_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                }
            }
        ),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "contract-intelligence-api"}


def company_or_404(
    db: Session, company_id: str | None = None, organization_id: str | None = None
) -> CompanyProfile:
    query = select(CompanyProfile)
    if company_id:
        query = query.where(CompanyProfile.id == company_id)
    if organization_id:
        query = query.where(CompanyProfile.organization_id == organization_id)
    company = db.scalar(query)
    if not company:
        raise HTTPException(
            404, detail={"code": "company_not_found", "message": "Company profile not found"}
        )
    return company


@app.get("/api/company", response_model=CompanyRead)
def get_company(
    principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> CompanyProfile:
    if principal.organization is None:
        raise HTTPException(
            403, detail={"code": "workspace_required", "message": "Select a company workspace"}
        )
    return company_or_404(db, organization_id=principal.organization.id)


@app.get("/api/company/{company_id}", response_model=CompanyRead)
def get_company_by_id(
    company_id: str,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> CompanyProfile:
    if principal.organization is None:
        raise HTTPException(
            403, detail={"code": "workspace_required", "message": "Select a company workspace"}
        )
    return company_or_404(db, company_id, principal.organization.id)


@app.post("/api/company", response_model=CompanyRead, status_code=201)
def create_company(
    payload: CompanyWrite,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> CompanyProfile:
    slug = payload.company_name.lower().replace(" ", "-")
    if db.scalar(select(Organization).where(Organization.slug == slug)):
        raise HTTPException(
            409, detail={"code": "company_exists", "message": "Organization slug already exists"}
        )
    org = Organization(name=payload.company_name, slug=slug)
    db.add(org)
    db.flush()
    company = CompanyProfile(organization_id=org.id, **payload.model_dump(mode="json"))
    db.add(company)
    db.add(
        OrganizationMember(
            organization_id=org.id, user_id=principal.user.id, role=MembershipRole.owner
        )
    )
    db.commit()
    db.refresh(company)
    return company


@app.post("/api/company/onboarding", response_model=CompanyRead, status_code=201)
def complete_company_onboarding(
    payload: CompanyWrite,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> CompanyProfile:
    assert principal.organization is not None
    existing = db.scalar(
        select(CompanyProfile).where(
            CompanyProfile.organization_id == principal.organization.id
        )
    )
    if existing is not None:
        raise HTTPException(
            409,
            detail={
                "code": "company_profile_exists",
                "message": "Company profile already exists",
            },
        )
    principal.organization.name = payload.company_name
    company = CompanyProfile(
        organization_id=principal.organization.id,
        **payload.model_dump(mode="json"),
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@app.put("/api/company/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: str,
    payload: CompanyWrite,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> CompanyProfile:
    assert principal.organization is not None
    company = company_or_404(db, company_id, principal.organization.id)
    for field, value in payload.model_dump(mode="json").items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company


@app.get("/api/opportunities", response_model=OpportunityPage)
def list_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    min_match_score: int | None = Query(None, ge=0, le=100),
    priority: str | None = None,
    source: str | None = None,
    geography: str | None = None,
    category: str | None = None,
    buyer: str | None = None,
    status: PipelineStatus | None = None,
    min_value: float | None = Query(None, ge=0),
    max_value: float | None = Query(None, ge=0),
    q: str | None = Query(None, min_length=2, max_length=200),
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if principal.organization is None:
        raise HTTPException(
            403, detail={"code": "workspace_required", "message": "Select a company workspace"}
        )
    company = company_or_404(db, organization_id=principal.organization.id)
    query = (
        select(Opportunity, OpportunityMatch)
        .join(
            OpportunityMatch,
            (OpportunityMatch.opportunity_id == Opportunity.id)
            & (OpportunityMatch.company_profile_id == company.id),
        )
        .options(joinedload(Opportunity.buyer))
    )
    if min_match_score is not None:
        query = query.where(OpportunityMatch.total_score >= min_match_score)
    if priority == "high":
        query = query.where(OpportunityMatch.total_score >= 85)
    elif priority == "medium":
        query = query.where(OpportunityMatch.total_score.between(65, 84))
    elif priority == "low":
        query = query.where(OpportunityMatch.total_score < 65)
    if source:
        query = query.where(func.lower(Opportunity.source) == source.lower())
    if geography:
        query = query.where(func.lower(Opportunity.region).contains(geography.lower()))
    if category:
        query = query.where(
            func.lower(func.cast(Opportunity.categories, String)).contains(category.lower())
        )
    if buyer:
        query = query.join(Buyer).where(func.lower(Buyer.name).contains(buyer.lower()))
    if status:
        query = query.where(Opportunity.status == status)
    if min_value is not None:
        query = query.where(Opportunity.estimated_value_max >= min_value)
    if max_value is not None:
        query = query.where(Opportunity.estimated_value_min <= max_value)
    if q:
        term = f"%{q.casefold()}%"
        text_filter = (
            func.lower(Opportunity.title).like(term)
            | func.lower(Opportunity.description).like(term)
            | func.lower(Opportunity.region).like(term)
            | func.lower(func.cast(Opportunity.categories, String)).like(term)
            | func.lower(func.cast(Opportunity.cpv_codes, String)).like(term)
        )
        if buyer:
            query = query.where(text_filter)
        else:
            query = query.join(Buyer).where(text_filter | func.lower(Buyer.name).like(term))
    rows = (
        db.execute(
            query.order_by(
                OpportunityMatch.total_score.desc(), Opportunity.estimated_value_max.desc()
            )
        )
        .unique()
        .all()
    )
    total = len(rows)
    rows = rows[(page - 1) * page_size : page * page_size]
    return {
        "items": [serialize_opportunity(opp, match) for opp, match in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@app.get("/api/opportunities/{opportunity_id}", response_model=OpportunityRead)
def get_opportunity(
    opportunity_id: str,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if principal.organization is None:
        raise HTTPException(
            403, detail={"code": "workspace_required", "message": "Select a company workspace"}
        )
    company = company_or_404(db, organization_id=principal.organization.id)
    row = (
        db.execute(
            select(Opportunity, OpportunityMatch)
            .join(
                OpportunityMatch,
                (OpportunityMatch.opportunity_id == Opportunity.id)
                & (OpportunityMatch.company_profile_id == company.id),
            )
            .where(Opportunity.id == opportunity_id)
            .options(joinedload(Opportunity.buyer))
        )
        .unique()
        .first()
    )
    if not row:
        raise HTTPException(
            404, detail={"code": "opportunity_not_found", "message": "Opportunity not found"}
        )
    return serialize_opportunity(row[0], row[1])


@app.get("/api/opportunities/{opportunity_id}/qualification", response_model=QualificationRead)
def get_qualification(
    opportunity_id: str,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if principal.organization is None:
        raise HTTPException(
            403, detail={"code": "workspace_required", "message": "Select a company workspace"}
        )
    company = company_or_404(db, organization_id=principal.organization.id)
    row = db.execute(
        select(Opportunity, OpportunityMatch)
        .join(OpportunityMatch)
        .where(
            Opportunity.id == opportunity_id,
            OpportunityMatch.company_profile_id == company.id,
        )
    ).first()
    if row is None:
        raise HTTPException(
            404, detail={"code": "opportunity_not_found", "message": "Opportunity not found"}
        )
    result = qualify_opportunity(row[0], row[1])
    return {
        "decision": result.decision,
        "reasons": result.reasons,
        "blockers": result.blockers,
        "version": result.version,
    }


@app.post("/api/opportunities/recalculate-matches", response_model=RecalculationResult)
def recalculate(
    principal: Principal = Depends(require_manager), db: Session = Depends(get_db)
) -> dict[str, object]:
    assert principal.organization is not None
    count = recalculate_matches(db, company_or_404(db, organization_id=principal.organization.id))
    logger.info("scores_recalculated count=%s version=%s", count, SCORING_VERSION)
    return {"recalculated": count, "scoring_version": SCORING_VERSION}


@app.patch("/api/opportunities/{opportunity_id}/status", response_model=OpportunityRead)
def update_status(
    opportunity_id: str,
    payload: StatusUpdate,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    assert principal.organization is not None
    company = company_or_404(db, organization_id=principal.organization.id)
    opportunity = db.scalar(
        select(Opportunity)
        .join(OpportunityMatch, OpportunityMatch.opportunity_id == Opportunity.id)
        .where(
            Opportunity.id == opportunity_id,
            OpportunityMatch.company_profile_id == company.id,
        )
    )
    if not opportunity:
        raise HTTPException(
            404, detail={"code": "opportunity_not_found", "message": "Opportunity not found"}
        )
    opportunity.status = payload.status
    db.commit()
    return get_opportunity(opportunity_id, principal, db)


@app.get("/api/dashboard/summary", response_model=DashboardSummary)
def dashboard(
    principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> dict[str, object]:
    if principal.organization is None:
        raise HTTPException(
            403, detail={"code": "workspace_required", "message": "Select a company workspace"}
        )
    company = company_or_404(db, organization_id=principal.organization.id)
    rows = db.execute(
        select(Opportunity, OpportunityMatch)
        .join(OpportunityMatch)
        .where(OpportunityMatch.company_profile_id == company.id)
    ).all()
    return dashboard_metrics([(row[0], row[1]) for row in rows])


@app.get("/api/buyers", response_model=list[BuyerIntelligence])
def buyers(_: Principal = Depends(current_principal), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    records = db.scalars(select(Buyer).options(joinedload(Buyer.opportunities))).unique().all()
    return [
        {
            "id": b.id,
            "source": b.source,
            "external_id": b.external_id,
            "name": b.name,
            "buyer_type": b.buyer_type,
            "description": b.description,
            "city": b.city,
            "region": b.region,
            "country": b.country,
            "website": b.website,
            "opportunity_count": len(b.opportunities),
            "active_opportunities": sum(
                o.status not in {PipelineStatus.won, PipelineStatus.lost, PipelineStatus.ignored}
                for o in b.opportunities
            ),
            "combined_visible_value": sum((opportunity_value(o) for o in b.opportunities), 0),
            "categories_observed": sorted({c for o in b.opportunities for c in o.categories}),
        }
        for b in records
    ]


@app.get("/api/buyers/{buyer_id}", response_model=BuyerIntelligence)
def buyer_detail(buyer_id: str, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)) -> dict[str, object]:
    results = [item for item in buyers(principal, db) if item["id"] == buyer_id]
    if not results:
        raise HTTPException(404, detail={"code": "buyer_not_found", "message": "Buyer not found"})
    return results[0]


@app.get("/api/buyers/{buyer_id}/opportunities", response_model=OpportunityPage)
def buyer_opportunities(
    buyer_id: str, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> dict[str, object]:
    if principal.organization is None:
        raise HTTPException(
            403, detail={"code": "workspace_required", "message": "Select a company workspace"}
        )
    company = company_or_404(db, organization_id=principal.organization.id)
    rows = (
        db.execute(
            select(Opportunity, OpportunityMatch)
            .join(
                OpportunityMatch,
                (OpportunityMatch.opportunity_id == Opportunity.id)
                & (OpportunityMatch.company_profile_id == company.id),
            )
            .where(Opportunity.buyer_id == buyer_id)
            .options(joinedload(Opportunity.buyer))
            .order_by(OpportunityMatch.total_score.desc())
        )
        .unique()
        .all()
    )
    return {
        "items": [serialize_opportunity(opp, match) for opp, match in rows],
        "total": len(rows),
        "page": 1,
        "page_size": len(rows) or 1,
    }


@app.get("/api/pipeline", response_model=list[PipelineItemRead])
def get_pipeline(
    principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    if principal.organization is None:
        raise HTTPException(
            403, detail={"code": "workspace_required", "message": "Select a company workspace"}
        )
    company = company_or_404(db, organization_id=principal.organization.id)
    return [
        serialize_pipeline_item(db, item, company.id)
        for item in pipeline_items(db, company.organization_id)
    ]


@app.get("/api/pipeline/summary", response_model=PipelineSummary)
def get_pipeline_summary(
    principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> dict[str, object]:
    if principal.organization is None:
        raise HTTPException(
            403, detail={"code": "workspace_required", "message": "Select a company workspace"}
        )
    company = company_or_404(db, organization_id=principal.organization.id)
    return pipeline_summary(pipeline_items(db, company.organization_id))


@app.post("/api/pipeline", response_model=PipelineItemRead, status_code=201)
def create_pipeline_item(
    payload: PipelineItemWrite,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    assert principal.organization is not None
    company = company_or_404(db, organization_id=principal.organization.id)
    try:
        item = add_pipeline_item(db, company.organization_id, payload)
    except LookupError as exc:
        raise HTTPException(
            404, detail={"code": str(exc), "message": "Opportunity not found"}
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            409,
            detail={"code": str(exc), "message": "Opportunity is already in the pipeline"},
        ) from exc
    return serialize_pipeline_item(db, item, company.id)


@app.patch("/api/pipeline/{item_id}", response_model=PipelineItemRead)
def patch_pipeline_item(
    item_id: str,
    payload: PipelineItemUpdate,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    assert principal.organization is not None
    company = company_or_404(db, organization_id=principal.organization.id)
    try:
        item = update_pipeline_item(db, company.organization_id, item_id, payload)
    except LookupError as exc:
        raise HTTPException(
            404, detail={"code": str(exc), "message": "Pipeline item not found"}
        ) from exc
    return serialize_pipeline_item(db, item, company.id)


@app.get("/api/saved-searches", response_model=list[SavedSearchRead])
def get_saved_searches(
    principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> list[SavedSearch]:
    if principal.organization is None:
        return []
    company = company_or_404(db, organization_id=principal.organization.id)
    return list(
        db.scalars(
            select(SavedSearch)
            .where(SavedSearch.organization_id == company.organization_id)
            .order_by(SavedSearch.created_at.desc())
        )
    )


@app.post("/api/saved-searches", response_model=SavedSearchRead, status_code=201)
def post_saved_search(
    payload: SavedSearchWrite,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> SavedSearch:
    assert principal.organization is not None
    company = company_or_404(db, organization_id=principal.organization.id)
    try:
        return create_saved_search(db, company.organization_id, payload)
    except ValueError as exc:
        raise HTTPException(
            409, detail={"code": str(exc), "message": "Saved-search name already exists"}
        ) from exc


@app.delete("/api/saved-searches/{search_id}", status_code=204)
def delete_saved_search(
    search_id: str, principal: Principal = Depends(require_manager), db: Session = Depends(get_db)
) -> None:
    assert principal.organization is not None
    company = company_or_404(db, organization_id=principal.organization.id)
    search = db.scalar(
        select(SavedSearch).where(
            SavedSearch.id == search_id,
            SavedSearch.organization_id == company.organization_id,
        )
    )
    if search is None:
        raise HTTPException(
            404,
            detail={"code": "saved_search_not_found", "message": "Saved search not found"},
        )
    db.delete(search)
    db.commit()


@app.get("/api/notifications", response_model=list[NotificationRead])
def get_notifications(
    principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> list[Notification]:
    if principal.organization is None:
        return []
    company = company_or_404(db, organization_id=principal.organization.id)
    return list(
        db.scalars(
            select(Notification)
            .where(
                Notification.organization_id == company.organization_id,
                (Notification.user_id.is_(None)) | (Notification.user_id == principal.user.id),
            )
            .order_by(Notification.created_at.desc())
        )
    )


@app.get("/api/activity", response_model=list[ActivityEventRead])
def get_activity(
    principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> list[ActivityEvent]:
    if principal.organization is None:
        return []
    company = company_or_404(db, organization_id=principal.organization.id)
    return list(
        db.scalars(
            select(ActivityEvent)
            .where(ActivityEvent.organization_id == company.organization_id)
            .order_by(ActivityEvent.created_at.desc())
            .limit(100)
        )
    )
