from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pandas as pd

from core.config import Settings


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Tao bo data quality checks theo Great Expectations 1.x."""
    quality_dir = settings.paths.quality_dir
    quality_dir.mkdir(parents=True, exist_ok=True)
    report_file = quality_dir / f"{report_name}_quality_report.json"

    # Rule checks manually to guarantee stability and detailed metrics
    total_rows = len(df)
    row_count_ok = 18 <= total_rows <= 30
    paper_id_not_null = bool(df["paper_id"].notna().all() and (df["paper_id"] != "").all()) if "paper_id" in df.columns else False
    title_not_null = bool(df["title"].notna().all() and (df["title"] != "").all()) if "title" in df.columns else False
    paper_id_unique = bool(df["paper_id"].is_unique) if "paper_id" in df.columns else False
    
    summary_len_ok = True
    if "summary" in df.columns:
        summary_len_ok = bool((df["summary"].astype(str).str.len() >= 20).all())

    # Try running Great Expectations 1.x
    gx_success = None
    gx_details = {}
    try:
        import great_expectations as gx
        import great_expectations.expectations as gxe

        context = gx.get_context(mode="ephemeral")
        data_source = context.data_sources.add_pandas(name=f"papers_source_{report_name}")
        data_asset = data_source.add_dataframe_asset(name=f"papers_asset_{report_name}")
        batch_def = data_asset.add_batch_definition_whole_dataframe(f"papers_batch_{report_name}")
        batch = batch_def.get_batch(batch_parameters={"dataframe": df})

        suite = gx.ExpectationSuite(name=f"papers_quality_suite_{report_name}")
        suite.add_expectation(gxe.ExpectTableRowCountToBeBetween(min_value=18, max_value=30))
        suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="paper_id"))
        suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="title"))
        suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="paper_id"))
        suite.add_expectation(gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=20))

        val_results = batch.validate(suite)
        gx_success = bool(val_results.success)
        gx_details = val_results.to_json_dict() if hasattr(val_results, "to_json_dict") else {}
    except Exception as exc:
        gx_details = {"warning": f"GX 1.x execution notice: {exc}"}

    overall_success = row_count_ok and paper_id_not_null and title_not_null and paper_id_unique and summary_len_ok
    if gx_success is not None:
        overall_success = overall_success and gx_success

    report: dict[str, Any] = {
        "success": bool(overall_success),
        "report_name": report_name,
        "total_rows": total_rows,
        "checks": {
            "row_count_between_18_and_30": row_count_ok,
            "paper_id_not_null": paper_id_not_null,
            "title_not_null": title_not_null,
            "paper_id_unique": paper_id_unique,
            "summary_length_ge_20": summary_len_ok,
        },
        "gx_1_x_validated": gx_success is not None,
        "gx_1_x_success": gx_success,
        "gx_details": gx_details,
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Tong hop freshness report theo Freshness SLA."""
    total_rows = len(df)
    if total_rows == 0:
        report = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": 0,
            "stale_ratio": 0.0,
            "is_fresh": False,
            "threshold_days": settings.freshness_threshold_days,
        }
    else:
        latest_published = str(df["published"].max())
        oldest_published = str(df["published"].min())
        stale_mask = df["age_days"] > settings.freshness_threshold_days
        stale_rows = int(stale_mask.sum())
        stale_ratio = stale_rows / total_rows
        # Freshness SLA: Canh bao is_fresh = False neu ty le bai bao co age_days > 180 vuot qua 25%
        is_fresh = stale_ratio <= 0.25
        report = {
            "latest_published": latest_published,
            "oldest_published": oldest_published,
            "stale_rows": stale_rows,
            "total_rows": total_rows,
            "stale_ratio": round(stale_ratio, 4),
            "is_fresh": is_fresh,
            "threshold_days": settings.freshness_threshold_days,
        }

    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report
