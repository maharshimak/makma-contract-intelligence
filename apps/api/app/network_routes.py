from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import Principal, current_principal, require_manager, require_platform_admin
from app.database import get_db
from app.models import (
    Application,
    CapabilityGap,
    CompanyProfile,
    Opportunity,
    Organization,
    OrganizationMember,
    ProfessionalProfile,
    User,
    WorkPost,
)
from app.network import (
    create_application,
    create_bid_team,
    create_work_post,
    opportunity_gaps,
    serialize_application,
    serialize_professional,
    serialize_work_post,
    team_recommendations,
)
from app.network_schemas import (
    AdminSummaryRead,
    ApplicationRead,
    ApplicationWrite,
    BidTeamRead,
    BidTeamWrite,
    CapabilityGapRead,
    ProfessionalRead,
    SessionRead,
    TeamRecommendationRead,
    WorkPostRead,
    WorkPostWrite,
    WorkspaceRead,
)

router = APIRouter(prefix="/api", tags=["network"])


@router.get("/session", response_model=SessionRead)
def session(
    principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> dict[str, object]:
    profile = db.scalar(
        select(ProfessionalProfile).where(ProfessionalProfile.user_id == principal.user.id)
    )
    rows = db.execute(
        select(OrganizationMember, Organization)
        .join(Organization, OrganizationMember.organization_id == Organization.id)
        .where(OrganizationMember.user_id == principal.user.id, OrganizationMember.status == "ACTIVE")
    ).all()
    workspace_values = [
        {"id": org.id, "name": org.name, "slug": org.slug, "role": membership.role,
         "organization_type": org.organization_type, "is_demo": org.is_demo}
        for membership, org in rows
    ]
    workspace = None
    if principal.organization and principal.membership:
        workspace = {
            "id": principal.organization.id,
            "name": principal.organization.name,
            "slug": principal.organization.slug,
            "role": principal.membership.role,
            "organization_type": principal.organization.organization_type,
            "is_demo": principal.organization.is_demo,
        }
    company = db.scalar(select(CompanyProfile).where(CompanyProfile.organization_id == principal.organization.id)) if principal.organization else None
    company_complete = company is not None and bool(company.description and company.service_categories)
    return {
        "user_id": principal.user.id,
        "email": principal.user.email,
        "display_name": principal.user.display_name,
        "platform_role": principal.user.platform_role,
        "active_workspace": workspace,
        "workspaces": workspace_values,
        "has_professional_profile": profile is not None,
        "company_profile_complete": company_complete,
        "onboarding_required": bool(principal.organization and not company_complete),
        "demo_session": principal.user.is_demo,
    }


@router.post("/session/workspace", status_code=204)
def switch_workspace(
    workspace_id: str,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> None:
    membership = db.scalar(select(OrganizationMember).where(
        OrganizationMember.user_id == principal.user.id,
        OrganizationMember.organization_id == workspace_id,
        OrganizationMember.status == "ACTIVE",
    ))
    if membership is None:
        raise HTTPException(403, detail={"code": "workspace_forbidden", "message": "User is not an active member of this workspace"})
    if principal.session is None:
        raise HTTPException(400, detail={"code": "session_required", "message": "Workspace switching requires a session"})
    principal.session.active_workspace_id = workspace_id
    db.commit()


@router.get("/workspaces", response_model=list[WorkspaceRead])
def workspaces(
    principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    rows = db.execute(
        select(OrganizationMember, Organization)
        .join(Organization, OrganizationMember.organization_id == Organization.id)
        .where(
            OrganizationMember.user_id == principal.user.id, OrganizationMember.status == "ACTIVE"
        )
    ).all()
    return [
        {
            "id": organization.id,
            "name": organization.name,
            "slug": organization.slug,
            "role": membership.role,
            "organization_type": organization.organization_type,
            "is_demo": organization.is_demo,
        }
        for membership, organization in rows
    ]


@router.get("/professionals/me", response_model=ProfessionalRead)
def my_professional_profile(
    principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> dict[str, object]:
    profile = db.scalar(
        select(ProfessionalProfile).where(ProfessionalProfile.user_id == principal.user.id)
    )
    if profile is None:
        raise HTTPException(
            404,
            detail={
                "code": "professional_profile_not_found",
                "message": "Professional profile not found",
            },
        )
    return serialize_professional(db, profile)


@router.get("/professionals", response_model=list[ProfessionalRead])
def professionals(
    _: Principal = Depends(require_manager), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    return [
        serialize_professional(db, profile)
        for profile in db.scalars(
            select(ProfessionalProfile).where(ProfessionalProfile.visibility != "PRIVATE")
        )
    ]


@router.get("/work-posts", response_model=list[WorkPostRead])
def work_posts(
    principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    profile = db.scalar(
        select(ProfessionalProfile).where(ProfessionalProfile.user_id == principal.user.id)
    )
    posts = db.scalars(
        select(WorkPost).where(WorkPost.status == "OPEN").order_by(WorkPost.created_at.desc())
    )
    return [serialize_work_post(db, post, profile) for post in posts]


@router.post("/work-posts", response_model=WorkPostRead, status_code=201)
def post_work_post(
    payload: WorkPostWrite,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return serialize_work_post(db, create_work_post(db, principal, payload))
    except LookupError as exc:
        raise HTTPException(
            404,
            detail={"code": str(exc), "message": "Linked opportunity or capability gap not found"},
        ) from exc


@router.post("/work-posts/{post_id}/applications", response_model=ApplicationRead, status_code=201)
def apply(
    post_id: str,
    payload: ApplicationWrite,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return serialize_application(db, create_application(db, principal, post_id, payload.note))
    except PermissionError as exc:
        raise HTTPException(
            403, detail={"code": str(exc), "message": "A professional profile is required"}
        ) from exc
    except LookupError as exc:
        raise HTTPException(
            404, detail={"code": str(exc), "message": "Open work post not found"}
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            409, detail={"code": str(exc), "message": "Application already exists"}
        ) from exc


@router.get("/applications/me", response_model=list[ApplicationRead])
def my_applications(
    principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    profile = db.scalar(
        select(ProfessionalProfile).where(ProfessionalProfile.user_id == principal.user.id)
    )
    if profile is None:
        return []
    return [
        serialize_application(db, application)
        for application in db.scalars(
            select(Application).where(Application.professional_profile_id == profile.id)
        )
    ]


@router.get("/work-posts/{post_id}/applications", response_model=list[ApplicationRead])
def post_applications(
    post_id: str, principal: Principal = Depends(require_manager), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    assert principal.organization is not None
    post = db.scalar(
        select(WorkPost).where(
            WorkPost.id == post_id, WorkPost.organization_id == principal.organization.id
        )
    )
    if post is None:
        raise HTTPException(
            404,
            detail={
                "code": "work_post_not_found",
                "message": "Work post not found in active workspace",
            },
        )
    return [
        serialize_application(db, application)
        for application in db.scalars(
            select(Application).where(Application.work_post_id == post_id)
        )
    ]


@router.get(
    "/opportunities/{opportunity_id}/capability-gaps", response_model=list[CapabilityGapRead]
)
def capability_gaps(
    opportunity_id: str,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> list[CapabilityGap]:
    assert principal.organization is not None
    return opportunity_gaps(db, principal.organization.id, opportunity_id)


@router.get(
    "/opportunities/{opportunity_id}/team-recommendations", response_model=TeamRecommendationRead
)
def recommendations(
    opportunity_id: str,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    assert principal.organization is not None
    if db.get(Opportunity, opportunity_id) is None:
        raise HTTPException(
            404, detail={"code": "opportunity_not_found", "message": "Opportunity not found"}
        )
    coverage, candidates = team_recommendations(db, principal.organization.id, opportunity_id)
    return {"current_coverage": coverage, "candidates": candidates}


@router.post(
    "/opportunities/{opportunity_id}/bid-team", response_model=BidTeamRead, status_code=201
)
def build_team(
    opportunity_id: str,
    payload: BidTeamWrite,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return create_bid_team(db, principal, opportunity_id, payload)
    except ValueError as exc:
        code = str(exc)
        raise HTTPException(
            409 if code == "bid_team_exists" else 422,
            detail={"code": code, "message": "Bid team could not be created"},
        ) from exc


@router.get("/admin/summary", response_model=AdminSummaryRead)
def admin_summary(
    _: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)
) -> dict[str, object]:
    return {
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "organizations": db.scalar(select(func.count()).select_from(Organization)) or 0,
        "professionals": db.scalar(select(func.count()).select_from(ProfessionalProfile)) or 0,
        "procurement_records": db.scalar(select(func.count()).select_from(Opportunity)) or 0,
        "open_work_posts": db.scalar(
            select(func.count()).select_from(WorkPost).where(WorkPost.status == "OPEN")
        )
        or 0,
        "demo_only": True,
    }
