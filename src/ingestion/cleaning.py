from __future__ import annotations

from datetime import datetime
import re
import pandas as pd

from ingestion.crossref import PaperRecord


def _clean_text(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", "", text)
    return " ".join(cleaned.split()).strip()


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed."""
    rows: list[dict] = []
    seen_ids: set[str] = set()

    run_d = run_date.date() if isinstance(run_date, datetime) else run_date

    for r in records:
        paper_id = (r.paper_id or "").strip()
        if not paper_id or paper_id in seen_ids:
            continue

        title = _clean_text(r.title)
        if not title:
            continue

        summary = _clean_text(r.summary)

        authors = [a.strip() for a in r.authors if a and a.strip()]
        authors_joined = ", ".join(authors) if authors else "Unknown"

        categories = [c.strip() for c in r.categories if c and c.strip()]
        categories_joined = ", ".join(categories) if categories else "General"
        primary_category = r.primary_category or (categories[0] if categories else "General")

        published = (r.published or "").strip()
        updated = (r.updated or "").strip() or published

        try:
            pub_date = datetime.strptime(published, "%Y-%m-%d").date()
            age_days = max(0, (run_d - pub_date).days)
        except Exception:
            age_days = 0

        # Cau truc 5 phan chuan hoa: Title, Authors, Categories, Published, Summary
        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Categories: {categories_joined}\n"
            f"Published: {published}\n"
            f"Summary: {summary}"
        )

        seen_ids.add(paper_id)
        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "published": published,
                "updated": updated,
                "abs_url": r.abs_url or f"https://doi.org/{paper_id}",
                "pdf_url": r.pdf_url or f"https://doi.org/{paper_id}",
                "comment": r.comment or f"Crossref record {paper_id}",
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": len(summary),
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by="published", ascending=False).reset_index(drop=True)
    return df
