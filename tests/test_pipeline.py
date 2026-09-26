from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import pytest

from core.config import load_settings
from core.utils import now_utc
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records, parse_crossref_payload
from observability.quality import build_freshness_report, run_data_quality_checks


@pytest.fixture
def settings():
    return load_settings()


@pytest.fixture
def raw_records(settings):
    return load_raw_records(settings.paths.raw_records_json)


@pytest.fixture
def clean_df(raw_records):
    return build_clean_dataframe(raw_records, now_utc())


def test_crossref_parser(settings):
    with open(settings.paths.raw_api_response, "r", encoding="utf-8") as f:
        payload = json.load(f)
    records = parse_crossref_payload(payload)
    assert len(records) == 24
    assert records[0].paper_id != ""
    assert records[0].title != ""


def test_clean_dataframe_pipeline(clean_df):
    assert len(clean_df) == 24
    assert "text_for_embedding" in clean_df.columns
    assert "age_days" in clean_df.columns
    assert "authors_joined" in clean_df.columns
    assert clean_df["paper_id"].is_unique
    # Check 5 parts of text_for_embedding
    sample_text = clean_df.iloc[0]["text_for_embedding"]
    assert "Title:" in sample_text
    assert "Authors:" in sample_text
    assert "Categories:" in sample_text
    assert "Published:" in sample_text
    assert "Summary:" in sample_text


def test_data_quality_gate(clean_df, settings):
    res = run_data_quality_checks(clean_df, settings, "test_baseline")
    assert res["success"] is True
    assert res["checks"]["row_count_between_18_and_30"] is True
    assert res["checks"]["paper_id_unique"] is True


def test_freshness_sla(clean_df, settings, tmp_path):
    report = build_freshness_report(clean_df, settings, tmp_path / "freshness.json")
    assert "is_fresh" in report
    assert report["total_rows"] == 24


def test_benchmark_testset_generation(clean_df, tmp_path):
    out_file = tmp_path / "test_set.json"
    questions = build_test_set(clean_df, out_file)
    assert len(questions) == 10
    types = {q["question_type"] for q in questions}
    assert {"summary", "authors", "date", "categories"}.issubset(types)


def test_data_corruption_impact(clean_df, settings, tmp_path):
    log_file = tmp_path / "corruption_log.json"
    corrupted_df = corrupt_clean_dataframe(clean_df, log_file)
    assert log_file.exists()
    # Check that quality gate fails on corrupted data
    res = run_data_quality_checks(corrupted_df, settings, "test_corrupted")
    assert res["success"] is False
