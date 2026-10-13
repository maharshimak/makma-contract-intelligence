from dataclasses import dataclass
from datetime import date

from app.models import Opportunity, OpportunityMatch

QUALIFICATION_VERSION = "v0.1-rules"


@dataclass(frozen=True)
class QualificationResult:
    decision: str
    reasons: list[str]
    blockers: list[str]
    version: str = QUALIFICATION_VERSION


def qualify_opportunity(
    opportunity: Opportunity, match: OpportunityMatch, today: date | None = None
) -> QualificationResult:
    current_date = today or date.today()
    days_left = (opportunity.deadline - current_date).days if opportunity.deadline else None
    blockers = list(match.missing_requirements)
    excluded = any("Excluded category" in reason for reason in match.risk_reasons)
    if excluded:
        blockers.append("Opportunity is in an explicitly excluded category.")
    if days_left is not None and days_left < 0:
        blockers.append("Deadline has passed.")

    reasons = [f"Deterministic match score is {match.total_score}/100."]
    if days_left is None:
        reasons.append("Deadline feasibility cannot be assessed because no deadline is recorded.")
    elif days_left < 7:
        reasons.append(f"Only {days_left} days remain before the deadline.")
    else:
        reasons.append(f"{days_left} days remain before the deadline.")

    if excluded or (days_left is not None and days_left < 0) or match.total_score < 50:
        decision = "NO-GO"
    elif match.total_score >= 85 and not blockers and (days_left is None or days_left >= 7):
        decision = "GO"
    elif match.total_score >= 70:
        decision = "CONDITIONAL GO"
    else:
        decision = "REVIEW"
    if blockers:
        reasons.append("Resolve recorded blockers before committing bid resources.")
    return QualificationResult(decision=decision, reasons=reasons, blockers=blockers)
