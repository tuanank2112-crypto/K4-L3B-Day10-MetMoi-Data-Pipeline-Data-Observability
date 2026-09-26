from __future__ import annotations

import pandas as pd

from core.config import load_settings
from ingestion.corruption import corrupt_clean_dataframe
from observability.self_healing import run_self_healing_gate


def main():
    print("=== DEMO AUTOMATED SELF-HEALING & AUTO-REPAIR (BONUS B2) ===")
    settings = load_settings()
    
    # 1. Load clean data and corrupt it
    print("Step 1: Loading clean data and simulating data corruption...")
    clean_df = pd.read_json(settings.paths.clean_json)
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    
    # 2. Feed corrupted data into Self-Healing Gate
    print("Step 2: Passing corrupted data to automated Self-Healing Gate...")
    result = run_self_healing_gate(corrupted_df, settings)
    
    if result.triggered and result.repaired_successfully:
        print("[SUCCESS] Automated Self-Healing pipeline caught all errors and fully restored data integrity!")
    else:
        print("[NOTICE] Pipeline finished with status:", result.details)


if __name__ == "__main__":
    main()
