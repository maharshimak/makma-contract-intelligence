from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class NormalizedBuyer:
    external_id: str
    name: str
    buyer_type: str | None = None
    city: str | None = None
    region: str | None = None
    country: str = "FR"
    website: str | None = None


@dataclass(frozen=True)
class NormalizedOpportunity:
    external_id: str
    title: str
    buyer: NormalizedBuyer
    description: str | None
    publication_date: datetime | None
    deadline: datetime | None
    estimated_value_min: Decimal | None
    estimated_value_max: Decimal | None
    currency: str
    cpv_codes: list[str]
    categories: list[str]
    location: str | None
    region: str | None
    procedure_type: str | None
    source_url: str | None
    source_updated_at: datetime | None
    quality_issues: list[str]


class ProcurementSourceAdapter(ABC):
    """Source-specific network and normalization boundary."""

    source_name: str
    normalization_version: str

    @abstractmethod
    def fetch_opportunities(self, limit: int = 25) -> list[dict[str, Any]]: ...

    @abstractmethod
    def normalize_opportunity(self, payload: dict[str, Any]) -> NormalizedOpportunity: ...

    @abstractmethod
    def health_check(self) -> bool: ...


class FutureSourceAdapter(ProcurementSourceAdapter):
    normalization_version = "not-implemented"

    def fetch_opportunities(self, limit: int = 25) -> list[dict[str, Any]]:
        raise NotImplementedError("External ingestion is not enabled for this source")

    def normalize_opportunity(self, payload: dict[str, Any]) -> NormalizedOpportunity:
        raise NotImplementedError("Source mapping is not implemented")

    def health_check(self) -> bool:
        return False
