from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any
import pandas as pd

from core.config import Settings, load_settings
from core.utils import now_utc, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from retrieval.index import LocalEmbeddingIndex

logger = logging.getLogger(__name__)


@dataclass
class HealingResult:
    triggered: bool
    initial_violations: list[str]
    repaired_successfully: bool
    repaired_df: pd.DataFrame
    details: dict[str, Any]


def run_self_healing_gate(
    df: pd.DataFrame,
    settings: Settings,
    collection_name: str | None = None,
) -> HealingResult:
    """Automated Self-Healing Gate:
    Tu dong kiem tra Data Quality & Freshness.
    Neu phat hien bat thuong (vi pham Quality Gate hoac Freshness SLA):
    -> Tu dong kich hoat luong khoi phuc (Self-Healing / Auto-Repair) tu nguon raw lineage.
    -> Tai lap lai index va xac thuc lai trang thai sach ma khong can can thiep thu cong.
    """
    collection = collection_name or settings.baseline_collection_name
    q_res = run_data_quality_checks(df, settings, "gate_pre_check")
    f_res = build_freshness_report(df, settings, settings.paths.quality_dir / "gate_freshness_check.json")

    violations: list[str] = []
    if not q_res.get("success", False):
        checks = q_res.get("checks", {})
        for name, passed in checks.items():
            if not passed:
                violations.append(f"Quality Check Failed: {name}")

    if not f_res.get("is_fresh", True):
        violations.append(
            f"Freshness SLA Breached: stale_ratio={f_res.get('stale_ratio')} > 0.25 (stale_rows={f_res.get('stale_rows')})"
        )

    if not violations:
        return HealingResult(
            triggered=False,
            initial_violations=[],
            repaired_successfully=True,
            repaired_df=df,
            details={"status": "Data is clean and compliant with SLA. No healing needed."},
        )

    print(f"\n[ALERT] Self-Healing Triggered! Detected {len(violations)} data health violations:")
    for v in violations:
        print(f"  - {v}")

    # 1. Rollback/Repair idempotently from raw snapshot
    print("[HEALING] Re-fetching clean raw lineage from data/raw/crossref_records.json...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, now_utc())

    # 2. Persist repaired artifacts
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    repaired_df.to_json(settings.paths.repaired_clean_json, orient="records", indent=2, force_ascii=False)

    # 3. Re-validate post-repair
    q_post = run_data_quality_checks(repaired_df, settings, "gate_post_repair")
    f_post = build_freshness_report(repaired_df, settings, settings.paths.quality_dir / "gate_post_freshness.json")
    repaired_ok = q_post.get("success", False) and f_post.get("is_fresh", False)

    # 4. Re-index vector store
    print("[HEALING] Rebuilding vector index for repaired dataset...")
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df, settings, embeddings_output_path=settings.paths.repaired_embeddings_json
    )

    heal_log = {
        "timestamp": now_utc().isoformat(),
        "violations": violations,
        "healing_action": "Idempotent Re-ingestion from raw lineage snapshot",
        "pre_repair_rows": len(df),
        "post_repair_rows": len(repaired_df),
        "post_repair_quality_success": q_post.get("success"),
        "post_repair_freshness_is_fresh": f_post.get("is_fresh"),
    }
    write_json(settings.paths.quality_dir / "self_healing_audit_log.json", heal_log)
    print(f"[HEALING COMPLETE] Quality Gate: {q_post.get('success')} | Freshness SLA: {f_post.get('is_fresh')}\n")

    return HealingResult(
        triggered=True,
        initial_violations=violations,
        repaired_successfully=repaired_ok,
        repaired_df=repaired_df,
        details=heal_log,
    )
