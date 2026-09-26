from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: str | Path) -> pd.DataFrame:
    """Simulate 6 dang data corruption theo yeu cau cua lab:
    1. Drop latest records (mat 20% ban ghi moi).
    2. Blank summary (xoa rong tom tat o mot so dong).
    3. Inject noise (chen ky tu rac vao tom tat).
    4. Truncate title (cat ngan tieu de < 8 ky tu).
    5. Stale date (lui ngay xuat ban ve qua khu de vi pham Freshness SLA).
    6. Duplicate rows (nhan ban du lieu de vi pham unique constraint).
    """
    cdf = df.copy()
    total_initial = len(cdf)
    log_details: dict = {
        "initial_rows": total_initial,
        "corruptions": {},
    }

    # 1. Drop 20% latest records (sorted by published desc)
    cdf = cdf.sort_values(by="published", ascending=False).reset_index(drop=True)
    drop_count = max(1, int(len(cdf) * 0.20))
    dropped_records = cdf.iloc[:drop_count]["paper_id"].tolist()
    cdf = cdf.iloc[drop_count:].reset_index(drop=True)
    log_details["corruptions"]["drop_latest"] = {
        "dropped_count": drop_count,
        "dropped_paper_ids": dropped_records,
    }

    # 2. Blank summary o 2 dong dau tien
    blank_targets = []
    if len(cdf) > 0:
        for idx in range(min(2, len(cdf))):
            pid = cdf.at[idx, "paper_id"]
            blank_targets.append(pid)
            cdf.at[idx, "summary"] = ""
            cdf.at[idx, "summary_chars"] = 0
    log_details["corruptions"]["blank_summary"] = {"affected_paper_ids": blank_targets}

    # 3. Inject noise vao summary o cac dong tiep theo
    noise_targets = []
    if len(cdf) > 4:
        for idx in [2, 3, 4]:
            pid = cdf.at[idx, "paper_id"]
            noise_targets.append(pid)
            cdf.at[idx, "summary"] = "### CORRUPTED_GARBAGE_NOISE_&&&_%%%_@@@ ### " * 3
            cdf.at[idx, "summary_chars"] = len(cdf.at[idx, "summary"])
    log_details["corruptions"]["inject_noise"] = {"affected_paper_ids": noise_targets}

    # 4. Truncate title < 8 ky tu
    trunc_targets = []
    if len(cdf) > 6:
        for idx in [5, 6]:
            pid = cdf.at[idx, "paper_id"]
            trunc_targets.append(pid)
            cdf.at[idx, "title"] = "ERR"
    log_details["corruptions"]["truncate_title"] = {"affected_paper_ids": trunc_targets}

    # 5. Stale date (lui ve 2018-01-01) tren 35% so dong con lai (vi pham SLA > 25%)
    stale_count = max(1, int(len(cdf) * 0.35))
    stale_targets = []
    for idx in range(stale_count):
        pid = cdf.at[idx, "paper_id"]
        stale_targets.append(pid)
        cdf.at[idx, "published"] = "2018-01-01"
        cdf.at[idx, "age_days"] = 3000
    log_details["corruptions"]["stale_dates"] = {
        "stale_count": stale_count,
        "affected_paper_ids": stale_targets,
    }

    # 6. Duplicate rows: nhan ban 3 dong
    dup_rows = []
    if len(cdf) >= 3:
        dups = cdf.iloc[:3].copy()
        dup_rows = dups["paper_id"].tolist()
        cdf = pd.concat([cdf, dups], ignore_index=True)
    log_details["corruptions"]["duplicate_rows"] = {"duplicated_paper_ids": dup_rows}

    # 7. Rebuild text_for_embedding
    cdf["text_for_embedding"] = cdf.apply(
        lambda r: (
            f"Title: {r['title']}\n"
            f"Authors: {r['authors_joined']}\n"
            f"Categories: {r['categories_joined']}\n"
            f"Published: {r['published']}\n"
            f"Summary: {r['summary']}"
        ),
        axis=1,
    )

    log_details["final_rows"] = len(cdf)

    # 8. Ghi corruption log
    out_path = Path(output_log_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(log_details, f, indent=2)

    return cdf
