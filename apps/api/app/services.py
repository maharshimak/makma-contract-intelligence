from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import CompanyProfile, Opportunity, OpportunityMatch, PipelineStatus
from app.scoring import SCORING_VERSION, priority_for, score_opportunity


def recalculate_matches(db: Session, company: CompanyProfile) -> int:
    opportunities = db.scalars(select(Opportunity).options(joinedload(Opportunity.buyer))).all()
    for opportunity in opportunities:
        result = score_opportunity(company, opportunity, opportunity.buyer)
        match = db.scalar(
            select(OpportunityMatch).where(
                OpportunityMatch.company_profile_id == company.id,
                OpportunityMatch.opportunity_id == opportunity.id,
            )
        ) or OpportunityMatch(
            company_profile_id=company.id,
            opportunity_id=opportunity.id,
            total_score=0,
            technical_score=0,
            geography_score=0,
            value_score=0,
            sector_score=0,
            buyer_score=0,
            eligibility_score=0,
            scoring_version=SCORING_VERSION,
        )
        for field, value in result.__dict__.items():
            setattr(match, field, value)
        match.calculated_at = datetime.now(UTC)
        db.add(match)
    db.commit()
    return len(opportunities)


def opportunity_value(opportunity: Opportunity) -> Decimal:
    if opportunity.estimated_value_min is not None and opportunity.estimated_value_max is not None:
        return (opportunity.estimated_value_min + opportunity.estimated_value_max) / 2
    return opportunity.estimated_value_max or opportunity.estimated_value_min or Decimal(0)


def dashboard_metrics(rows: list[tuple[Opportunity, OpportunityMatch]]) -> dict[str, object]:
    today = date.today()
    active = [
        (opp, match)
        for opp, match in rows
        if opp.status not in {PipelineStatus.won, PipelineStatus.lost, PipelineStatus.ignored}
        and (opp.deadline is None or opp.deadline >= today)
    ]
    # Matched pipeline excludes low-priority records; midpoint avoids overstating ranges.
    matched = [(opp, match) for opp, match in active if match.total_score >= 65]
    deadlines = [(opp.deadline - today).days for opp, _ in active if opp.deadline is not None]
    values = [opportunity_value(opp) for opp, _ in active]
    return {
        "total_matched_pipeline": sum((opportunity_value(opp) for opp, _ in matched), Decimal(0)),
        "high_priority_count": sum(match.total_score >= 85 for _, match in active),
        "medium_priority_count": sum(65 <= match.total_score < 85 for _, match in active),
        "low_priority_count": sum(match.total_score < 65 for _, match in active),
        "active_opportunities": len(active),
        "average_match_score": round(sum(match.total_score for _, match in active) / len(active), 1)
        if active
        else 0,
        "closing_in_7_days": sum(0 <= days <= 7 for days in deadlines),
        "closing_in_30_days": sum(0 <= days <= 30 for days in deadlines),
        "largest_opportunity": max(values) if values else None,
        "nearest_deadline_days": min((days for days in deadlines if days >= 0), default=None),
    }


def serialize_match(match: OpportunityMatch | None) -> dict[str, object] | None:
    if not match:
        return None
    fields = [
        "total_score",
        "technical_score",
        "geography_score",
        "value_score",
        "sector_score",
        "buyer_score",
        "eligibility_score",
        "positive_reasons",
        "risk_reasons",
        "missing_requirements",
        "scoring_version",
        "calculated_at",
    ]
    data = {field: getattr(match, field) for field in fields}
    data["priority"] = priority_for(match.total_score)
    return data


def serialize_opportunity(
    opportunity: Opportunity, match: OpportunityMatch | None
) -> dict[str, object]:
    return {
        column.name: getattr(opportunity, column.name)
        for column in Opportunity.__table__.columns
        if column.name not in {"buyer_id", "raw_metadata", "created_at", "updated_at"}
    } | {"buyer": opportunity.buyer, "match": serialize_match(match)}
