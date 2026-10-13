import json
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from html import unescape
from typing import Any

from app.adapters.base import FutureSourceAdapter, NormalizedBuyer, NormalizedOpportunity
from app.config import get_settings

JsonFetcher = Callable[[str, float], dict[str, Any]]


def _fetch_json(url: str, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "PublicRevenueOS/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError("BOAMP returned a non-object response")
    return value


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [unescape(str(item)).strip() for item in value if item not in (None, "")]
    return [unescape(str(value)).strip()]


def _text(value: object) -> str:
    return unescape(str(value or "")).strip()


def _nested_json(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _walk(node: object) -> list[tuple[str, object]]:
    values: list[tuple[str, object]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            values.append((key, value))
            values.extend(_walk(value))
    elif isinstance(node, list):
        for value in node:
            values.extend(_walk(value))
    return values


def _eforms_values(payload: dict[str, Any]) -> tuple[Decimal | None, str, list[str], str | None]:
    data = _nested_json(payload, "donnees")
    amount: Decimal | None = None
    currency = "EUR"
    cpv_codes: set[str] = set()
    description: str | None = None
    for key, value in _walk(data):
        if key == "cbc:EstimatedOverallContractAmount" and isinstance(value, dict):
            try:
                candidate = Decimal(str(value.get("#text")))
                amount = max(amount or candidate, candidate)
                currency = str(value.get("@currencyID") or currency)
            except (InvalidOperation, TypeError):
                pass
        elif key == "cbc:ItemClassificationCode" and isinstance(value, dict):
            if value.get("@listName") == "cpv" and value.get("#text"):
                cpv_codes.add(str(value["#text"]))
        elif key == "cbc:Description" and description is None:
            if isinstance(value, dict) and value.get("#text"):
                description = _text(value["#text"])
            elif isinstance(value, str):
                description = _text(value)
    return amount, currency, sorted(cpv_codes), description


class BoampAdapter:
    """BOAMP Opendatasoft v2.1 adapter using only source-owned field names."""

    source_name = "BOAMP"
    normalization_version = "boamp-v2"

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        fetcher: JsonFetcher = _fetch_json,
    ) -> None:
        settings = get_settings()
        self.base_url = base_url or settings.boamp_api_url
        self.timeout = timeout or settings.procurement_http_timeout_seconds
        self.fetcher = fetcher

    def fetch_opportunities(self, limit: int = 25) -> list[dict[str, Any]]:
        if not 1 <= limit <= 100:
            raise ValueError("BOAMP fetch limit must be between 1 and 100")
        query = urllib.parse.urlencode({"limit": limit, "order_by": "dateparution desc"})
        response = self.fetcher(f"{self.base_url}?{query}", self.timeout)
        records = response.get("results")
        if not isinstance(records, list):
            raise ValueError("BOAMP response is missing a results list")
        return [record for record in records if isinstance(record, dict)]

    def normalize_opportunity(self, payload: dict[str, Any]) -> NormalizedOpportunity:
        external_id = _text(payload.get("idweb"))
        title = _text(payload.get("objet"))
        buyer_name = _text(payload.get("nomacheteur"))
        issues = [
            message
            for missing, message in [
                (not external_id, "missing_external_id"),
                (not title, "missing_title"),
                (not buyer_name, "missing_buyer"),
                (not payload.get("datelimitereponse"), "missing_deadline"),
            ]
            if missing
        ]
        if not external_id or not title or not buyer_name:
            raise ValueError(",".join(issues))
        amount, currency, cpv_codes, description = _eforms_values(payload)
        buyer_key = sha256(" ".join(buyer_name.casefold().split()).encode()).hexdigest()[:24]
        departments = _as_list(
            payload.get("code_departement_prestation") or payload.get("code_departement")
        )
        return NormalizedOpportunity(
            external_id=external_id,
            title=title,
            buyer=NormalizedBuyer(external_id=f"name-{buyer_key}", name=buyer_name),
            description=description,
            publication_date=_parse_datetime(payload.get("dateparution")),
            deadline=_parse_datetime(payload.get("datelimitereponse")),
            estimated_value_min=amount,
            estimated_value_max=amount,
            currency=currency,
            cpv_codes=cpv_codes,
            categories=_as_list(payload.get("descripteur_libelle")),
            location=", ".join(departments) or None,
            region=None,
            procedure_type=_text(
                payload.get("procedure_libelle") or payload.get("type_procedure")
            )
            or None,
            source_url=str(payload.get("url_avis") or "") or None,
            source_updated_at=_parse_datetime(payload.get("datefindiffusion")),
            quality_issues=issues,
        )

    def health_check(self) -> bool:
        try:
            return bool(self.fetch_opportunities(limit=1))
        except (OSError, ValueError):
            return False


class TedAdapter(FutureSourceAdapter):
    source_name = "TED"


class ApprochAdapter(FutureSourceAdapter):
    source_name = "APPROCH"


class DecpAdapter(FutureSourceAdapter):
    source_name = "DECP"
