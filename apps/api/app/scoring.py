from dataclasses import dataclass
from decimal import Decimal

from app.models import Buyer, CompanyProfile, Opportunity

SCORING_VERSION = "v0.1-deterministic"
WEIGHTS = {
    "technical": 30,
    "value": 20,
    "geography": 15,
    "sector": 15,
    "buyer": 10,
    "eligibility": 10,
}
PRIORITY_THRESHOLDS = {"high": 85, "medium": 65}


def _norm(values: list[str]) -> set[str]:
    return {value.strip().casefold() for value in values if value.strip()}


def _overlap(left: list[str], right: list[str]) -> set[str]:
    return _norm(left) & _norm(right)


@dataclass(frozen=True)
class ScoreResult:
    total_score: int
    technical_score: int
    value_score: int
    geography_score: int
    sector_score: int
    buyer_score: int
    eligibility_score: int
    positive_reasons: list[str]
    risk_reasons: list[str]
    missing_requirements: list[str]
    scoring_version: str = SCORING_VERSION


def priority_for(score: int) -> str:
    if score >= PRIORITY_THRESHOLDS["high"]:
        return "high"
    if score >= PRIORITY_THRESHOLDS["medium"]:
        return "medium"
    return "low"


def score_opportunity(
    company: CompanyProfile, opportunity: Opportunity, buyer: Buyer
) -> ScoreResult:
    positives: list[str] = []
    risks: list[str] = []

    tech_overlap = _overlap(
        company.technologies + company.service_categories,
        opportunity.technologies + opportunity.categories,
    )
    target_tech = _norm(opportunity.technologies + opportunity.categories)
    technical = (
        round(WEIGHTS["technical"] * min(1, len(tech_overlap) / max(1, min(4, len(target_tech)))))
        if target_tech
        else 15
    )
    if tech_overlap:
        positives.append(f"Relevant capability overlap: {', '.join(sorted(tech_overlap)[:5])}.")
    elif target_tech:
        risks.append("No explicit technology or service overlap was found.")

    low, high = opportunity.estimated_value_min, opportunity.estimated_value_max
    pref_low, pref_high = company.preferred_contract_min, company.preferred_contract_max
    value = 10 if low is None and high is None else 0
    if pref_low is not None and pref_high is not None and (low is not None or high is not None):
        opp_low = low if low is not None else high
        opp_high = high if high is not None else low
        assert opp_low is not None and opp_high is not None
        if opp_high >= pref_low and opp_low <= pref_high:
            value = WEIGHTS["value"]
            positives.append("Contract value overlaps the preferred commercial range.")
            if opp_high >= pref_high * Decimal("0.9"):
                risks.append("Contract value is close to the upper preferred limit.")
        elif opp_high < pref_low:
            ratio = float(opp_high / pref_low) if pref_low else 0
            value = round(WEIGHTS["value"] * min(0.6, ratio))
            risks.append("Contract value is below the preferred range.")
        else:
            ratio = float(pref_high / opp_low) if opp_low else 0
            value = round(WEIGHTS["value"] * min(0.6, ratio))
            risks.append("Contract value exceeds the preferred range.")

    geos = _norm(company.preferred_geographies + company.operating_regions)
    opp_geos = _norm([opportunity.region or "", opportunity.country, opportunity.location or ""])
    geography = (
        WEIGHTS["geography"]
        if geos & opp_geos or "france" in geos and opportunity.country == "FR"
        else 2
    )
    if geography == WEIGHTS["geography"]:
        positives.append(
            f"Opportunity is in a preferred geography ({opportunity.region or opportunity.country})."
        )
    else:
        risks.append("Opportunity geography is outside the stated preferences.")

    excluded = _overlap(company.excluded_categories, opportunity.categories)
    category_overlap = _overlap(
        company.preferred_categories + company.service_categories, opportunity.categories
    )
    if excluded:
        sector = 0
        risks.append(f"Excluded category: {', '.join(sorted(excluded))}.")
    elif category_overlap:
        sector = WEIGHTS["sector"]
        positives.append(f"Preferred category overlap: {', '.join(sorted(category_overlap))}.")
    elif opportunity.categories:
        sector = 4
        risks.append("Category is not in the company's preferred sectors.")
    else:
        sector = 7

    buyer_types = _norm(company.preferred_buyer_types)
    buyer_type = (buyer.buyer_type or "").casefold()
    buyer_score = WEIGHTS["buyer"] if not buyer_types or buyer_type in buyer_types else 4
    if buyer_types and buyer_score == WEIGHTS["buyer"]:
        positives.append(f"{buyer.buyer_type} is a preferred buyer type.")
    elif buyer_types:
        risks.append(f"{buyer.buyer_type or 'Unknown buyer type'} is not a preferred buyer type.")

    required = _norm(opportunity.certifications_required)
    held = _norm(company.certifications)
    missing = sorted(required - held)
    if not required:
        eligibility = WEIGHTS["eligibility"]
        positives.append("No explicit certification gap is recorded.")
    elif not missing:
        eligibility = WEIGHTS["eligibility"]
        positives.append("All recorded certification requirements are met.")
    else:
        eligibility = round(WEIGHTS["eligibility"] * len(required & held) / len(required))
        risks.append(f"Missing recorded certification requirements: {', '.join(missing)}.")

    scores = [technical, value, geography, sector, buyer_score, eligibility]
    return ScoreResult(
        sum(scores),
        technical,
        value,
        geography,
        sector,
        buyer_score,
        eligibility,
        positives,
        risks,
        missing,
    )
