from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, write_csv
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Xay dung baseline pipeline end-to-end."""
    settings = load_settings()

    # 1. Fetch hoac load raw records
    print("[1/6] Ingesting raw Crossref records...")
    raw_records = fetch_source_records(settings)

    # 2. Clean data
    print("[2/6] Cleaning raw records and constructing text_for_embedding...")
    run_date = now_utc()
    clean_df = build_clean_dataframe(raw_records, run_date)

    # 3. Save clean CSV and JSON
    print("[3/6] Saving clean artifacts...")
    write_csv(clean_df, settings.paths.clean_csv)
    settings.paths.clean_json.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_json(settings.paths.clean_json, orient="records", indent=2, force_ascii=False)

    # 4. Build Chroma index
    print("[4/6] Indexing vector embeddings with ChromaDB...")
    index = LocalEmbeddingIndex.build(clean_df, settings, embeddings_output_path=settings.paths.embeddings_json)

    # 5. Build test set if needed
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        print("[5/6] Generating benchmark test set (10 questions)...")
        build_test_set(clean_df, settings.paths.eval_testset)
    else:
        print("[5/6] Using existing benchmark test set...")

    # 6. Evaluate baseline
    print("[6/6] Evaluating baseline RAG pipeline and generating reports...")
    eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    # Observability: Great Expectations 1.x & Freshness SLA
    quality_report = run_data_quality_checks(clean_df, settings, report_name="baseline")
    freshness_report = build_freshness_report(clean_df, settings, settings.paths.freshness_report)

    # Generate Markdown Report
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "total_records": len(raw_records),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=eval_bundle.summary,
        quality=quality_report,
        freshness=freshness_report,
    )

    print("\n=== BASELINE PIPELINE EXECUTION SUCCESSFUL ===")
    print(f"Clean Rows: {len(clean_df)}")
    print(f"Data Quality Gate Success: {quality_report.get('success')}")
    print(f"Freshness SLA is_fresh: {freshness_report.get('is_fresh')}")
    print(f"Retrieval Hit Rate: {eval_bundle.summary.get('retrieval_hit_rate'):.4f}")
    print(f"Mean Token F1: {eval_bundle.summary.get('mean_token_f1'):.4f}")
    print(f"Report Generated: {settings.paths.baseline_report}")
