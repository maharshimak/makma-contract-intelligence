from decimal import Decimal
from types import SimpleNamespace

from app.scoring import priority_for, score_opportunity


def company(**overrides):
    data = dict(
        technologies=["Python", "RAG", "NLP"],
        service_categories=["Artificial Intelligence"],
        certifications=["AWS"],
        preferred_contract_min=Decimal("100000"),
        preferred_contract_max=Decimal("1500000"),
        preferred_geographies=["France", "Île-de-France"],
        operating_regions=[],
        preferred_categories=["Artificial Intelligence"],
        excluded_categories=["Cleaning"],
        preferred_buyer_types=["hospital"],
    )
    data.update(overrides)
    return SimpleNamespace(**data)


def opportunity(**overrides):
    data = dict(
        technologies=["Python", "RAG", "NLP"],
        categories=["Artificial Intelligence"],
        certifications_required=[],
        estimated_value_min=Decimal("200000"),
        estimated_value_max=Decimal("500000"),
        region="Île-de-France",
        country="FR",
        location="Paris",
    )
    data.update(overrides)
    return SimpleNamespace(**data)


def buyer(kind="hospital"):
    return SimpleNamespace(buyer_type=kind)


def test_perfect_match_is_high_priority():
    result = score_opportunity(company(), opportunity(), buyer())
    assert result.total_score == 100
    assert priority_for(result.total_score) == "high"


def test_zero_or_excluded_match_is_low():
    result = score_opportunity(
        company(),
        opportunity(
            technologies=["SAP"],
            categories=["Cleaning"],
            region="Berlin",
            country="DE",
            location="Berlin",
            estimated_value_min=Decimal("5000000"),
            estimated_value_max=Decimal("6000000"),
            certifications_required=["ISO 27001"],
        ),
        buyer("city"),
    )
    assert result.total_score < 35
    assert any("Excluded category" in reason for reason in result.risk_reasons)


def test_missing_values_are_neutral_not_fabricated():
    result = score_opportunity(
        company(),
        opportunity(
            technologies=[],
            categories=[],
            estimated_value_min=None,
            estimated_value_max=None,
            region=None,
            location=None,
        ),
        buyer(),
    )
    assert result.value_score == 10
    assert result.sector_score == 7


def test_below_and_above_range_are_penalized():
    below = score_opportunity(
        company(),
        opportunity(estimated_value_min=Decimal("40000"), estimated_value_max=Decimal("50000")),
        buyer(),
    )
    above = score_opportunity(
        company(),
        opportunity(estimated_value_min=Decimal("3000000"), estimated_value_max=Decimal("4000000")),
        buyer(),
    )
    assert below.value_score < 20 and above.value_score < 20
    assert any("below" in r for r in below.risk_reasons)
    assert any("exceeds" in r for r in above.risk_reasons)


def test_partial_technology_overlap_and_geography_mismatch():
    result = score_opportunity(
        company(),
        opportunity(
            technologies=["Python", "Go", "Rust", "Java"],
            region="Bavaria",
            country="DE",
            location="Munich",
        ),
        buyer(),
    )
    assert 0 < result.technical_score < 30
    assert result.geography_score == 2


def test_missing_certification_is_explicit():
    result = score_opportunity(
        company(), opportunity(certifications_required=["AWS", "ISO 27001"]), buyer()
    )
    assert result.eligibility_score == 5
    assert result.missing_requirements == ["iso 27001"]
