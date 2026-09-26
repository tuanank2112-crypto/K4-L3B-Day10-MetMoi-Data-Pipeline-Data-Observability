from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pandas as pd

from core.utils import first_sentence


def build_test_set(df: pd.DataFrame, output_path: str | Path) -> list[dict[str, Any]]:
    """Tao bo evaluation set 10 cau hoi tu cleaned dataframe phu 4 nhom nghiep vu:
    summary, authors, date, categories.
    """
    if df.empty:
        raise ValueError("Cannot build test set from empty dataframe.")

    num_records = len(df)
    questions: list[dict[str, Any]] = []

    # 10 cau hoi can doi: 3 summary, 3 authors, 2 date, 2 categories
    plan = [
        ("summary", "Summarize the paper '{title}'."),
        ("authors", "Who authored the paper '{title}'?"),
        ("date", "When was the paper '{title}' published?"),
        ("categories", "What categories describe the paper '{title}'?"),
        ("summary", "Can you summarize the paper '{title}'?"),
        ("authors", "List the authors of the paper '{title}'."),
        ("date", "When was the publication date of '{title}'?"),
        ("categories", "What categories are associated with the paper '{title}'?"),
        ("summary", "Briefly summarize the research in '{title}'."),
        ("authors", "Who authored the study '{title}'?"),
    ]

    for idx, (q_type, q_template) in enumerate(plan):
        row_idx = idx % num_records
        row = df.iloc[row_idx]
        title = row["title"]
        paper_id = row["paper_id"]

        if q_type == "summary":
            gt = first_sentence(str(row["summary"]))
        elif q_type == "authors":
            gt = str(row["authors_joined"])
        elif q_type == "date":
            gt = str(row["published"])
        elif q_type == "categories":
            gt = str(row["categories_joined"])
        else:
            gt = first_sentence(str(row["summary"]))

        questions.append(
            {
                "id": f"q_{idx + 1:02d}",
                "question_type": q_type,
                "question": q_template.format(title=title),
                "ground_truth": gt,
                "ground_truth_doc_ids": [paper_id],
            }
        )

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    return questions
