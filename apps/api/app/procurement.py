import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.base import NormalizedOpportunity
from app.adapters.sources import BoampAdapter
from app.models import (
    Buyer,
    CompanyProfile,
    Opportunity,
    PipelineStatus,
    ProcurementIngestionRun,
    RawProcurementRecord,
    utcnow,
)
from app.services import recalculate_matches


class SourceAdapter(Protocol):
    source_name: str
    normalization_version: str

    def fetch_opportunities(self, limit: int = 25) -> list[dict[str, Any]]: ...

    def normalize_opportunity(self, payload: dict[str, Any]) -> NormalizedOpportunity: ...


@dataclass(frozen=True)
class IngestionResult:
    run_id: str
    source: str
    status: str
    fetched: int
    created: int
    updated: int
    unchanged: int
    rejected: int
    matches_recalculated: int


def payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _date(value: datetime | None) -> date | None:
    return value.date() if value else None


def _upsert_buyer(db: Session, normalized: NormalizedOpportunity, source: str) -> Buyer:
    buyer = db.scalar(
        select(Buyer).where(
            Buyer.source == source,
            Buyer.external_id == normalized.buyer.external_id,
        )
    )
    if buyer is None:
        buyer = Buyer(source=source, external_id=normalized.buyer.external_id)
    buyer.name = normalized.buyer.name
    buyer.buyer_type = normalized.buyer.buyer_type
    buyer.city = normalized.buyer.city
    buyer.region = normalized.buyer.region
    buyer.country = normalized.buyer.country
    buyer.website = normalized.buyer.website
    buyer.raw_metadata = {"provenance": "SOURCE_DERIVED", "identity_basis": "normalized_name"}
    db.add(buyer)
    db.flush()
    return buyer


def _opportunity_values(
    normalized: NormalizedOpportunity,
    buyer: Buyer,
    source: str,
    normalization_version: str,
    ingested_at: datetime,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source": source,
        "external_id": normalized.external_id,
        "title": normalized.title,
        "description": normalized.description,
        "buyer_id": buyer.id,
        "publication_date": _date(normalized.publication_date),
        "deadline": _date(normalized.deadline),
        "estimated_value_min": normalized.estimated_value_min,
        "estimated_value_max": normalized.estimated_value_max,
        "currency": normalized.currency,
        "cpv_codes": normalized.cpv_codes,
        "categories": normalized.categories,
        "technologies": [],
        "certifications_required": [],
        "location": normalized.location,
        "region": normalized.region,
        "country": "FR",
        "procedure_type": normalized.procedure_type,
        "source_url": normalized.source_url,
        "raw_metadata": {
            "source_schema": payload.get("source_schema"),
            "notice_type": payload.get("nature_libelle"),
            "criteria": payload.get("criteres") or [],
            "provenance": "SOURCE_DERIVED",
        },
        "data_classification": "SOURCE_DERIVED",
        "source_published_at": normalized.publication_date,
        "source_updated_at": normalized.source_updated_at,
        "ingested_at": ingested_at,
        "normalization_version": normalization_version,
        "is_demo": False,
    }


def ingest_source(db: Session, adapter: SourceAdapter, limit: int = 25) -> IngestionResult:
    run = ProcurementIngestionRun(source=adapter.source_name, requested_limit=limit)
    db.add(run)
    db.commit()
    try:
        payloads = adapter.fetch_opportunities(limit)
    except Exception as exc:
        run.status = "FAILED"
        run.error_message = str(exc)[:2000]
        run.finished_at = utcnow()
        db.commit()
        raise

    created = updated = unchanged = rejected = 0
    run.fetched_count = len(payloads)
    for payload in payloads:
        digest = payload_hash(payload)
        external_id = str(payload.get("idweb") or f"missing-{digest[:24]}")
        raw = db.scalar(
            select(RawProcurementRecord).where(
                RawProcurementRecord.source == adapter.source_name,
                RawProcurementRecord.external_id == external_id,
                RawProcurementRecord.payload_hash == digest,
            )
        )
        if (
            raw is not None
            and raw.processing_status == "PROCESSED"
            and raw.normalization_version == adapter.normalization_version
        ):
            unchanged += 1
            continue
        if raw is None:
            raw = RawProcurementRecord(
                source=adapter.source_name,
                external_id=external_id,
                source_url=str(payload.get("url_avis") or "") or None,
                raw_payload=payload,
                payload_hash=digest,
                normalization_version=adapter.normalization_version,
                processing_status="PROCESSING",
            )
            db.add(raw)
            db.flush()
        else:
            raw.processing_status = "PROCESSING"
            raw.normalization_version = adapter.normalization_version
        try:
            normalized = adapter.normalize_opportunity(payload)
            raw.source_published_at = normalized.publication_date
            raw.source_updated_at = normalized.source_updated_at
            raw.quality_issues = normalized.quality_issues
            raw.quality_status = "WARNING" if normalized.quality_issues else "VALID"
            buyer = _upsert_buyer(db, normalized, adapter.source_name)
            opportunity = db.scalar(
                select(Opportunity).where(
                    Opportunity.source == adapter.source_name,
                    Opportunity.external_id == normalized.external_id,
                )
            )
            values = _opportunity_values(
                normalized, buyer, adapter.source_name, adapter.normalization_version, utcnow(), payload
            )
            if opportunity is None:
                deadline = normalized.deadline
                values["status"] = (
                    PipelineStatus.ignored
                    if deadline is not None and deadline < datetime.now(UTC)
                    else PipelineStatus.discovered
                )
                opportunity = Opportunity(**values)
                created += 1
            else:
                for field, value in values.items():
                    setattr(opportunity, field, value)
                updated += 1
            db.add(opportunity)
            db.flush()
            raw.opportunity_id = opportunity.id
            raw.processing_status = "PROCESSED"
            raw.processed_at = utcnow()
        except (TypeError, ValueError) as exc:
            rejected += 1
            raw.processing_status = "REJECTED"
            raw.quality_status = "INVALID"
            raw.quality_issues = [part for part in str(exc).split(",") if part]
            raw.processed_at = utcnow()
        db.commit()

    matches_recalculated = 0
    if created or updated:
        for company in db.scalars(select(CompanyProfile)):
            matches_recalculated += recalculate_matches(db, company)
    run.status = "COMPLETED"
    run.created_count = created
    run.updated_count = updated
    run.unchanged_count = unchanged
    run.rejected_count = rejected
    run.finished_at = utcnow()
    db.commit()
    return IngestionResult(
        run_id=run.id,
        source=run.source,
        status=run.status,
        fetched=len(payloads),
        created=created,
        updated=updated,
        unchanged=unchanged,
        rejected=rejected,
        matches_recalculated=matches_recalculated,
    )


def ingest_boamp(db: Session, limit: int = 25) -> IngestionResult:
    return ingest_source(db, BoampAdapter(), limit)


def source_status(db: Session) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in ["BOAMP", "TED", "APPROCH", "DECP"]:
        latest = db.scalar(
            select(ProcurementIngestionRun)
            .where(ProcurementIngestionRun.source == source)
            .order_by(ProcurementIngestionRun.started_at.desc())
        )
        raw_count = db.scalar(
            select(func.count()).select_from(RawProcurementRecord).where(
                RawProcurementRecord.source == source
            )
        )
        opportunity_count = db.scalar(
            select(func.count()).select_from(Opportunity).where(Opportunity.source == source)
        )
        rows.append(
            {
                "source": source,
                "implemented": source == "BOAMP",
                "raw_records": raw_count or 0,
                "opportunities": opportunity_count or 0,
                "latest_run": (
                    {
                        "id": latest.id,
                        "status": latest.status,
                        "started_at": latest.started_at,
                        "finished_at": latest.finished_at,
                        "fetched": latest.fetched_count,
                        "created": latest.created_count,
                        "updated": latest.updated_count,
                        "unchanged": latest.unchanged_count,
                        "rejected": latest.rejected_count,
                        "error": latest.error_message,
                    }
                    if latest
                    else None
                ),
            }
        )
    return rows
