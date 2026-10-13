from datetime import date, timedelta
from types import SimpleNamespace

from app.qualification import qualify_opportunity


def test_go_requires_strong_match_no_blockers_and_time():
    opportunity = SimpleNamespace(deadline=date.today() + timedelta(days=20))
    match = SimpleNamespace(total_score=90, missing_requirements=[], risk_reasons=[])
    assert qualify_opportunity(opportunity, match).decision == "GO"


def test_missing_requirement_makes_decision_conditional():
    opportunity = SimpleNamespace(deadline=date.today() + timedelta(days=20))
    match = SimpleNamespace(total_score=90, missing_requirements=["iso 27001"], risk_reasons=[])
    result = qualify_opportunity(opportunity, match)
    assert result.decision == "CONDITIONAL GO"
    assert result.blockers == ["iso 27001"]


def test_expired_or_excluded_is_no_go():
    opportunity = SimpleNamespace(deadline=date.today() - timedelta(days=1))
    match = SimpleNamespace(
        total_score=95, missing_requirements=[], risk_reasons=["Excluded category: cleaning."]
    )
    assert qualify_opportunity(opportunity, match).decision == "NO-GO"
