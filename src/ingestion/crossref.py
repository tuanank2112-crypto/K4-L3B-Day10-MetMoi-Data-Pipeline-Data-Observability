from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
import re
import time
import requests

from core.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_text(text: str) -> str:
    if not text:
        return ""
    # Strip XML/HTML tags like <jats:p>, </jats:p>, etc.
    cleaned = re.sub(r"<[^>]+>", "", text)
    # Collapse multiple whitespaces into a single space
    return " ".join(cleaned.split()).strip()


def _format_date(date_data: dict) -> str:
    if not date_data or not isinstance(date_data, dict):
        return ""
    date_parts = date_data.get("date-parts", [])
    if date_parts and isinstance(date_parts, list) and len(date_parts) > 0:
        first_part = date_parts[0]
        if isinstance(first_part, list) and len(first_part) > 0:
            year = first_part[0]
            month = first_part[1] if len(first_part) > 1 else 1
            day = first_part[2] if len(first_part) > 2 else 1
            return f"{year:04d}-{month:02d}-{day:02d}"
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        paper_id = item.get("DOI", "").strip()
        if not paper_id:
            continue

        raw_title = item.get("title", "")
        if isinstance(raw_title, list):
            title = _clean_text(raw_title[0]) if raw_title else ""
        else:
            title = _clean_text(str(raw_title))

        raw_abstract = item.get("abstract", "")
        summary = _clean_text(raw_abstract)

        authors: list[str] = []
        for author in item.get("author", []):
            if isinstance(author, dict):
                given = author.get("given", "").strip()
                family = author.get("family", "").strip()
                name = f"{given} {family}".strip()
                if name:
                    authors.append(name)

        categories = [str(s).strip() for s in item.get("subject", []) if str(s).strip()]
        primary_category = categories[0] if categories else ""

        published = _format_date(item.get("published", {}))
        updated = _format_date(item.get("updated", {})) or published

        url = item.get("URL", f"https://doi.org/{paper_id}")
        abs_url = url
        pdf_url = url
        comment = f"Crossref record {paper_id}"

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi source API, luu raw response, parse thanh records."""
    settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)

    payload: dict | None = None

    if settings.refresh_source:
        url = "https://api.crossref.org/works"
        params = {
            "query": settings.source_query,
            "filter": settings.source_filter,
            "rows": settings.max_results,
        }
        headers = {
            "User-Agent": "VinLab-RAG-Observability/1.0 (mailto:student@vinuni.edu.vn)"
        }
        for attempt in range(3):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=15)
                if response.status_code == 200:
                    payload = response.json()
                    with open(settings.paths.raw_api_response, "w", encoding="utf-8") as f:
                        json.dump(payload, f, ensure_ascii=False, indent=2)
                    break
                elif response.status_code in {429, 503}:
                    time.sleep(2 * (attempt + 1))
                else:
                    break
            except Exception as e:
                logger.warning("Error fetching from Crossref API (attempt %d): %s", attempt + 1, e)
                time.sleep(1)

    if payload is None:
        # Fallback to local snapshot
        if settings.paths.raw_api_response.exists():
            with open(settings.paths.raw_api_response, "r", encoding="utf-8") as f:
                payload = json.load(f)
        elif settings.paths.raw_records_json.exists():
            return load_raw_records(settings.paths.raw_records_json)
        else:
            raise FileNotFoundError(
                f"Neither online source nor offline fallback found at {settings.paths.raw_api_response}"
            )

    records = parse_crossref_payload(payload)

    # Save to raw_records_json to ensure lineage
    with open(settings.paths.raw_records_json, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, ensure_ascii=False, indent=2)

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh `PaperRecord`."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [PaperRecord(**item) for item in data]
