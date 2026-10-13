from dataclasses import asdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import Principal, require_platform_admin
from app.database import get_db
from app.procurement import ingest_boamp, source_status

router = APIRouter(prefix="/api/admin/procurement", tags=["procurement-admin"])


@router.get("/sources")
def procurement_sources(
    _: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    return source_status(db)


@router.post("/boamp/ingest")
def run_boamp_ingestion(
    limit: int = Query(25, ge=1, le=100),
    _: Principal = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return asdict(ingest_boamp(db, limit))
