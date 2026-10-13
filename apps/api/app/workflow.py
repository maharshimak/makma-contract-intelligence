from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import ActivityEvent, Opportunity, PipelineItem, SavedSearch
from app.schemas import PipelineItemUpdate, PipelineItemWrite, SavedSearchWrite
from app.services import opportunity_value, serialize_opportunity


def add_pipeline_item(
    db: Session, organization_id: str, payload: PipelineItemWrite
) -> PipelineItem:
    opportunity = db.get(Opportunity, payload.opportunity_id)
    if opportunity is None:
        raise LookupError("opportunity_not_found")
    existing = db.scalar(
        select(PipelineItem).where(
            PipelineItem.organization_id == organization_id,
            PipelineItem.opportunity_id == payload.opportunity_id,
        )
    )
    if existing is not None:
        raise ValueError("pipeline_item_exists")
    values = payload.model_dump()
    if values["value"] is None:
        values["value"] = opportunity_value(opportunity)
    item = PipelineItem(organization_id=organization_id, **values)
    db.add(item)
    db.flush()
    db.add(
        ActivityEvent(
            organization_id=organization_id,
            action="pipeline.added",
            entity_type="pipeline_item",
            entity_id=item.id,
            event_metadata={"opportunity_id": opportunity.id, "stage": item.stage.value},
        )
    )
    db.commit()
    return pipeline_item(db, organization_id, item.id)


def update_pipeline_item(
    db: Session, organization_id: str, item_id: str, payload: PipelineItemUpdate
) -> PipelineItem:
    item = db.scalar(
        select(PipelineItem).where(
            PipelineItem.id == item_id, PipelineItem.organization_id == organization_id
        )
    )
    if item is None:
        raise LookupError("pipeline_item_not_found")
    changes = payload.model_dump(exclude_unset=True)
    previous_stage = item.stage.value
    for field, value in changes.items():
        setattr(item, field, value)
    db.add(
        ActivityEvent(
            organization_id=organization_id,
            action="pipeline.updated",
            entity_type="pipeline_item",
            entity_id=item.id,
            event_metadata={"previous_stage": previous_stage, "stage": item.stage.value},
        )
    )
    db.commit()
    return pipeline_item(db, organization_id, item.id)


def pipeline_item(db: Session, organization_id: str, item_id: str) -> PipelineItem:
    item = db.scalar(
        select(PipelineItem)
        .where(PipelineItem.id == item_id, PipelineItem.organization_id == organization_id)
        .options(
            joinedload(PipelineItem.opportunity).joinedload(Opportunity.buyer),
            joinedload(PipelineItem.opportunity).joinedload(Opportunity.matches),
        )
    )
    if item is None:
        raise LookupError("pipeline_item_not_found")
    return item


def pipeline_items(db: Session, organization_id: str) -> list[PipelineItem]:
    return list(
        db.scalars(
            select(PipelineItem)
            .where(PipelineItem.organization_id == organization_id)
            .options(
                joinedload(PipelineItem.opportunity).joinedload(Opportunity.buyer),
                joinedload(PipelineItem.opportunity).joinedload(Opportunity.matches),
            )
            .order_by(PipelineItem.updated_at.desc())
        ).unique()
    )


def serialize_pipeline_item(
    db: Session, item: PipelineItem, company_profile_id: str
) -> dict[str, object]:
    match = next(
        (
            candidate
            for candidate in item.opportunity.matches
            if candidate.company_profile_id == company_profile_id
        ),
        None,
    )
    return {
        "id": item.id,
        "organization_id": item.organization_id,
        "opportunity_id": item.opportunity_id,
        "stage": item.stage,
        "value": item.value,
        "probability": item.probability,
        "next_action": item.next_action,
        "next_action_date": item.next_action_date,
        "notes": item.notes,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "opportunity": serialize_opportunity(item.opportunity, match),
    }


def pipeline_summary(items: list[PipelineItem]) -> dict[str, object]:
    total = sum((item.value or Decimal(0) for item in items), Decimal(0))
    weighted = sum(
        ((item.value or Decimal(0)) * Decimal(item.probability or 0) / 100 for item in items),
        Decimal(0),
    )
    stages: dict[str, int] = {}
    for item in items:
        stages[item.stage.value] = stages.get(item.stage.value, 0) + 1
    return {
        "total_value": total,
        "weighted_value": weighted,
        "item_count": len(items),
        "by_stage": stages,
    }


def create_saved_search(
    db: Session, organization_id: str, payload: SavedSearchWrite
) -> SavedSearch:
    existing = db.scalar(
        select(SavedSearch).where(
            SavedSearch.organization_id == organization_id, SavedSearch.name == payload.name
        )
    )
    if existing is not None:
        raise ValueError("saved_search_exists")
    search = SavedSearch(organization_id=organization_id, **payload.model_dump())
    db.add(search)
    db.flush()
    db.add(
        ActivityEvent(
            organization_id=organization_id,
            action="saved_search.created",
            entity_type="saved_search",
            entity_id=search.id,
            event_metadata={"name": search.name},
        )
    )
    db.commit()
    db.refresh(search)
    return search
