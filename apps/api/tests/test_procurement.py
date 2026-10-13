from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.adapters.sources import BoampAdapter
from app.models import (
    Buyer,
    Opportunity,
    OpportunityMatch,
    ProcurementIngestionRun,
    RawProcurementRecord,
)
from app.procurement import IngestionResult, ingest_source
from conftest import TestingSession
from sqlalchemy import delete, func, select


def boamp_record(title: str = "Plateforme de données hospitalières") -> dict[str, Any]:
    return {
        "idweb": "26-TEST-001",
        "objet": title,
        "nomacheteur": "Centre hospitalier de test",
        "dateparution": "2026-08-13",
        "datefindiffusion": "2026-09-30",
        "datelimitereponse": "2026-09-15T09:59:00+00:00",
        "procedure_libelle": "Procédure Ouverte",
        "descripteur_libelle": ["Informatique"],
        "code_departement": ["75"],
        "source_schema": "3.2.5",
        "nature_libelle": "Avis de marché",
        "criteres": ["environnementaux"],
        "url_avis": "https://www.boamp.fr/pages/avis/?q=idweb:26-TEST-001",
        "donnees": {
            "EFORMS": {
                "cbc:Description": {"#text": "Modernisation vérifiable des données."},
                "cbc:EstimatedOverallContractAmount": {
                    "@currencyID": "EUR",
                    "#text": "1200000",
                },
                "cbc:ItemClassificationCode": {"@listName": "cpv", "#text": "72200000"},
            }
        },
    }


class FixtureAdapter(BoampAdapter):
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.records = records

    def fetch_opportunities(self, limit: int = 25) -> list[dict[str, Any]]:
        return self.records[:limit]


@pytest.fixture
def cleanup_boamp() -> Generator[None, None, None]:
    yield
    with TestingSession() as db:
        opportunity_ids = list(
            db.scalars(select(Opportunity.id).where(Opportunity.source == "BOAMP"))
        )
        if opportunity_ids:
            db.execute(
                delete(OpportunityMatch).where(
                    OpportunityMatch.opportunity_id.in_(opportunity_ids)
                )
            )
        db.execute(delete(RawProcurementRecord).where(RawProcurementRecord.source == "BOAMP"))
        db.execute(delete(Opportunity).where(Opportunity.source == "BOAMP"))
        db.execute(delete(Buyer).where(Buyer.source == "BOAMP"))
        db.execute(
            delete(ProcurementIngestionRun).where(ProcurementIngestionRun.source == "BOAMP")
        )
        db.commit()


def test_boamp_adapter_fetch_and_normalize() -> None:
    captured: dict[str, object] = {}

    def fetcher(url: str, timeout: float) -> dict[str, Any]:
        captured.update(url=url, timeout=timeout)
        return {"results": [boamp_record()]}

    adapter = BoampAdapter(base_url="https://boamp.test/records", timeout=7, fetcher=fetcher)
    payload = adapter.fetch_opportunities(limit=1)[0]
    payload["nomacheteur"] = "Service d&#039;incendie"
    normalized = adapter.normalize_opportunity(payload)
    assert "limit=1" in str(captured["url"])
    assert "order_by=dateparution+desc" in str(captured["url"])
    assert normalized.external_id == "26-TEST-001"
    assert normalized.estimated_value_max == Decimal("1200000")
    assert normalized.cpv_codes == ["72200000"]
    assert normalized.deadline == datetime(2026, 9, 15, 9, 59, tzinfo=UTC)
    assert normalized.categories == ["Informatique"]
    assert normalized.buyer.name == "Service d'incendie"


def test_ingestion_retains_raw_data_deduplicates_and_updates(cleanup_boamp: None) -> None:
    invalid = boamp_record()
    invalid["idweb"] = ""
    with TestingSession() as db:
        first = ingest_source(db, FixtureAdapter([boamp_record(), invalid]), limit=2)
        assert (first.created, first.rejected, first.unchanged) == (1, 1, 0)
        opportunity = db.scalar(select(Opportunity).where(Opportunity.source == "BOAMP"))
        assert opportunity is not None
        assert opportunity.is_demo is False
        assert opportunity.data_classification == "SOURCE_DERIVED"
        assert opportunity.normalization_version == "boamp-v2"
        assert db.scalar(select(func.count()).select_from(RawProcurementRecord)) == 2

        second = ingest_source(db, FixtureAdapter([boamp_record()]), limit=1)
        assert (second.created, second.updated, second.unchanged) == (0, 0, 1)
        assert db.scalar(select(func.count()).select_from(RawProcurementRecord)) == 2

        replay_adapter = FixtureAdapter([boamp_record()])
        replay_adapter.normalization_version = "boamp-v3-test"
        replay = ingest_source(db, replay_adapter, limit=1)
        assert (replay.created, replay.updated, replay.unchanged) == (0, 1, 0)
        assert db.scalar(select(func.count()).select_from(RawProcurementRecord)) == 2

        changed = boamp_record("Plateforme de données hospitalières — rectificatif")
        third = ingest_source(db, FixtureAdapter([changed]), limit=1)
        assert (third.created, third.updated) == (0, 1)
        db.refresh(opportunity)
        assert opportunity.title.endswith("rectificatif")
        assert db.scalar(select(func.count()).select_from(RawProcurementRecord)) == 3


def test_procurement_admin_routes_are_protected(client, monkeypatch) -> None:
    assert client.get("/api/admin/procurement/sources").status_code == 403
    headers = {"X-Demo-User": "user-e3945303@example.test"}
    status = client.get("/api/admin/procurement/sources", headers=headers)
    assert status.status_code == 200
    assert status.json()[0]["source"] == "BOAMP"

    result = IngestionResult("run-1", "BOAMP", "COMPLETED", 1, 1, 0, 0, 0, 2)
    monkeypatch.setattr("app.procurement_routes.ingest_boamp", lambda db, limit: result)
    response = client.post("/api/admin/procurement/boamp/ingest?limit=1", headers=headers)
    assert response.status_code == 200
    assert response.json()["matches_recalculated"] == 2
