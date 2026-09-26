from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import read_json
from observability.dashboard import generate_interactive_html_dashboard


def main():
    print("=== GENERATING INTERACTIVE OBSERVABILITY DASHBOARD (BONUS B1) ===")
    settings = load_settings()
    clean_df = pd.read_json(settings.paths.clean_json) if settings.paths.clean_json.exists() else pd.DataFrame()
    baseline_metrics = read_json(settings.paths.baseline_metrics) if settings.paths.baseline_metrics.exists() else {}
    corrupted_metrics = read_json(settings.paths.corrupted_metrics) if settings.paths.corrupted_metrics.exists() else {}
    repaired_metrics = read_json(settings.paths.repaired_metrics) if settings.paths.repaired_metrics.exists() else {}
    
    out_file = generate_interactive_html_dashboard(
        settings=settings,
        clean_df=clean_df,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_metrics,
        repaired_metrics=repaired_metrics,
    )
    print(f"[SUCCESS] Dashboard generated at: {out_file}")


if __name__ == "__main__":
    main()
