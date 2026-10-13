from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Principal
from app.models import (
    Application,
    AuditLog,
    BidTeam,
    BidTeamMember,
    CapabilityGap,
    CompanyProfile,
    Opportunity,
    Organization,
    ProfessionalProfile,
    User,
    WorkPost,
)
from app.network_schemas import BidTeamWrite, TeamCandidateRead, WorkPostWrite


def _normalized(values: Iterable[str]) -> set[str]:
    return {value.casefold().strip() for value in values}


def profile_strength(profile: ProfessionalProfile) -> int:
    fields = [
        profile.headline,
        profile.bio,
        profile.location,
        profile.skills,
        profile.technologies,
        profile.certifications,
        profile.languages,
        profile.years_experience,
        profile.availability_status,
        profile.preferred_engagements,
        profile.portfolio_items,
    ]
    return round(sum(bool(value) for value in fields) / len(fields) * 100)


def serialize_professional(db: Session, profile: ProfessionalProfile) -> dict[str, object]:
    user = db.get(User, profile.user_id)
    if user is None:
        raise LookupError("professional_user_not_found")
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "display_name": user.display_name,
        "headline": profile.headline,
        "bio": profile.bio,
        "location": profile.location,
        "country": profile.country,
        "skills": profile.skills,
        "technologies": profile.technologies,
        "certifications": profile.certifications,
        "industries": profile.industries,
        "procurement_experience": profile.procurement_experience,
        "years_experience": profile.years_experience,
        "availability_status": profile.availability_status,
        "daily_rate": profile.daily_rate,
        "preferred_engagements": profile.preferred_engagements,
        "remote_preference": profile.remote_preference,
        "profile_strength": profile_strength(profile),
        "is_demo": profile.is_demo,
    }


def serialize_work_post(
    db: Session, post: WorkPost, profile: ProfessionalProfile | None = None
) -> dict[str, object]:
    organization = db.get(Organization, post.organization_id)
    opportunity = db.get(Opportunity, post.opportunity_id) if post.opportunity_id else None
    professional_capabilities = _normalized(
        (profile.skills + profile.technologies + profile.certifications) if profile else []
    )
    required = post.required_skills + post.required_certifications
    matched = [value for value in required if value.casefold() in professional_capabilities]
    missing = [value for value in required if value.casefold() not in professional_capabilities]
    return {
        "id": post.id,
        "organization_id": post.organization_id,
        "organization_name": organization.name if organization else "Unknown",
        "post_type": post.post_type,
        "title": post.title,
        "summary": post.summary,
        "opportunity_id": post.opportunity_id,
        "opportunity_title": opportunity.title if opportunity else None,
        "location": post.location,
        "remote_policy": post.remote_policy,
        "required_skills": post.required_skills,
        "required_certifications": post.required_certifications,
        "compensation_min": post.compensation_min,
        "compensation_max": post.compensation_max,
        "currency": post.currency,
        "contingent_on_award": post.contingent_on_award,
        "status": post.status,
        "is_demo": post.is_demo,
        "match_reasons": [f"Matched {value}" for value in matched],
        "missing_skills": missing,
        "created_at": post.created_at,
    }


def create_work_post(db: Session, principal: Principal, payload: WorkPostWrite) -> WorkPost:
    assert principal.organization is not None
    if payload.opportunity_id and db.get(Opportunity, payload.opportunity_id) is None:
        raise LookupError("opportunity_not_found")
    if payload.capability_gap_id:
        gap = db.scalar(
            select(CapabilityGap).where(
                CapabilityGap.id == payload.capability_gap_id,
                CapabilityGap.organization_id == principal.organization.id,
            )
        )
        if gap is None:
            raise LookupError("capability_gap_not_found")
    post = WorkPost(
        organization_id=principal.organization.id,
        created_by=principal.user.id,
        is_demo=True,
        **payload.model_dump(),
    )
    db.add(post)
    db.flush()
    db.add(
        AuditLog(
            organization_id=principal.organization.id,
            actor_user_id=principal.user.id,
            action="work_post.created",
            entity_type="work_post",
            entity_id=post.id,
            audit_metadata={
                "post_type": post.post_type.value,
                "contingent": post.contingent_on_award,
            },
        )
    )
    db.commit()
    db.refresh(post)
    return post


def create_application(
    db: Session, principal: Principal, post_id: str, note: str | None
) -> Application:
    profile = db.scalar(
        select(ProfessionalProfile).where(ProfessionalProfile.user_id == principal.user.id)
    )
    post = db.get(WorkPost, post_id)
    if profile is None:
        raise PermissionError("professional_profile_required")
    if post is None or post.status != "OPEN":
        raise LookupError("work_post_not_found")
    if db.scalar(
        select(Application).where(
            Application.work_post_id == post_id, Application.professional_profile_id == profile.id
        )
    ):
        raise ValueError("application_exists")
    application = Application(work_post_id=post_id, professional_profile_id=profile.id, note=note)
    db.add(application)
    db.flush()
    db.add(
        AuditLog(
            organization_id=post.organization_id,
            actor_user_id=principal.user.id,
            action="application.submitted",
            entity_type="application",
            entity_id=application.id,
            audit_metadata={"work_post_id": post_id},
        )
    )
    db.commit()
    db.refresh(application)
    return application


def serialize_application(db: Session, application: Application) -> dict[str, object]:
    post = db.get(WorkPost, application.work_post_id)
    profile = db.get(ProfessionalProfile, application.professional_profile_id)
    user = db.get(User, profile.user_id) if profile else None
    return {
        "id": application.id,
        "work_post_id": application.work_post_id,
        "work_post_title": post.title if post else "Unknown",
        "professional_profile_id": application.professional_profile_id,
        "professional_name": user.display_name if user else "Unknown",
        "status": application.status,
        "note": application.note,
        "created_at": application.created_at,
    }


def opportunity_gaps(db: Session, organization_id: str, opportunity_id: str) -> list[CapabilityGap]:
    return list(
        db.scalars(
            select(CapabilityGap)
            .where(
                CapabilityGap.organization_id == organization_id,
                CapabilityGap.opportunity_id == opportunity_id,
            )
            .order_by(CapabilityGap.coverage_weight.desc())
        )
    )


def current_coverage(gaps: list[CapabilityGap]) -> int:
    return max(0, 100 - sum(gap.coverage_weight for gap in gaps if gap.resolution_status == "OPEN"))


def team_recommendations(
    db: Session, organization_id: str, opportunity_id: str
) -> tuple[int, list[TeamCandidateRead]]:
    gaps = opportunity_gaps(db, organization_id, opportunity_id)
    gap_capabilities = {gap.id: gap.capability.casefold() for gap in gaps}
    candidates: list[TeamCandidateRead] = []
    for profile in db.scalars(
        select(ProfessionalProfile).where(ProfessionalProfile.visibility != "PRIVATE")
    ):
        user = db.get(User, profile.user_id)
        capabilities = (
            profile.skills
            + profile.technologies
            + profile.certifications
            + profile.procurement_experience
        )
        normalized = _normalized(capabilities)
        resolved = [
            gap_id
            for gap_id, capability in gap_capabilities.items()
            if capability in normalized
            or any(capability in item or item in capability for item in normalized)
        ]
        if resolved and user:
            weight = sum(gap.coverage_weight for gap in gaps if gap.id in resolved)
            candidates.append(
                TeamCandidateRead(
                    candidate_type="PROFESSIONAL",
                    candidate_id=profile.id,
                    name=user.display_name,
                    headline=profile.headline,
                    suitability=min(99, 70 + weight),
                    capabilities=capabilities,
                    resolves_gap_ids=resolved,
                    is_demo=profile.is_demo,
                )
            )
    profiles = db.execute(
        select(CompanyProfile, Organization)
        .join(Organization, CompanyProfile.organization_id == Organization.id)
        .where(Organization.id != organization_id)
    ).all()
    for company, organization in profiles:
        capabilities = company.service_categories + company.technologies + company.certifications
        normalized = _normalized(capabilities)
        resolved = [
            gap_id
            for gap_id, capability in gap_capabilities.items()
            if capability in normalized
            or any(capability in item or item in capability for item in normalized)
        ]
        if resolved:
            weight = sum(gap.coverage_weight for gap in gaps if gap.id in resolved)
            candidates.append(
                TeamCandidateRead(
                    candidate_type="PARTNER",
                    candidate_id=organization.id,
                    name=organization.name,
                    headline="Verified capability partner"
                    if organization.verification_status == "VERIFIED"
                    else "Network capability partner",
                    suitability=min(99, 72 + weight),
                    capabilities=capabilities,
                    resolves_gap_ids=resolved,
                    is_demo=organization.is_demo,
                )
            )
    candidates.sort(key=lambda item: (-item.suitability, item.name))
    return current_coverage(gaps), candidates


def create_bid_team(
    db: Session, principal: Principal, opportunity_id: str, payload: BidTeamWrite
) -> dict[str, object]:
    assert principal.organization is not None
    coverage, available = team_recommendations(db, principal.organization.id, opportunity_id)
    lookup = {(item.candidate_type, item.candidate_id): item for item in available}
    selected: list[TeamCandidateRead] = []
    for member in payload.members:
        candidate = lookup.get((member.candidate_type, member.candidate_id))
        if candidate is None:
            raise ValueError("invalid_team_candidate")
        selected.append(candidate)
    existing = db.scalar(
        select(BidTeam).where(
            BidTeam.organization_id == principal.organization.id,
            BidTeam.opportunity_id == opportunity_id,
        )
    )
    if existing:
        raise ValueError("bid_team_exists")
    team = BidTeam(
        organization_id=principal.organization.id,
        opportunity_id=opportunity_id,
        created_by=principal.user.id,
        name=payload.name,
    )
    db.add(team)
    db.flush()
    for candidate in selected:
        db.add(
            BidTeamMember(
                bid_team_id=team.id,
                member_type=candidate.candidate_type,
                member_id=candidate.candidate_id,
                display_name=candidate.name,
                capabilities=candidate.capabilities,
            )
        )
    resolved_ids = {gap_id for candidate in selected for gap_id in candidate.resolves_gap_ids}
    gaps = opportunity_gaps(db, principal.organization.id, opportunity_id)
    proposed = min(
        100, coverage + sum(gap.coverage_weight for gap in gaps if gap.id in resolved_ids)
    )
    db.add(
        AuditLog(
            organization_id=principal.organization.id,
            actor_user_id=principal.user.id,
            action="bid_team.draft_created",
            entity_type="bid_team",
            entity_id=team.id,
            audit_metadata={"member_count": len(selected), "proposed_coverage": proposed},
        )
    )
    db.commit()
    db.refresh(team)
    return {
        "id": team.id,
        "opportunity_id": opportunity_id,
        "name": team.name,
        "status": team.status,
        "current_coverage": coverage,
        "proposed_coverage": proposed,
        "members": selected,
        "created_at": team.created_at,
    }
