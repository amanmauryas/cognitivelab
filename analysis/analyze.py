"""Stroop Behavioral Experiment Analysis Script.

This script extracts trial-level psychometric data from the SQLite database,
applies behavioral data cleaning rules, computes summary statistics,
and generates a visualization comparing Congruent vs. Incongruent reaction times.

Usage:
    python analysis/analyze.py
"""
import json
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "psychometrics.db"
OUTPUT_DIR = BASE_DIR / "analysis"
OUTPUT_IMAGE = OUTPUT_DIR / "stroop_effect.png"

# Data Cleaning Thresholds (Reaction Time in milliseconds)
# Anticipation: Motor response initiated before cognitive processing is physiologically plausible (< 200 ms)
RT_MIN_THRESHOLD_MS = 200.0
# Attentional lapse: Trials where participant likely paused or lost fixation (> 2,500 ms)
RT_MAX_THRESHOLD_MS = 2500.0


def load_raw_data(db_path: Path) -> pd.DataFrame:
    """Connect to SQLite and extract all test trials joined with test sessions and users."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}")

    conn = sqlite3.connect(db_path)
    query = """
        SELECT
            u.participant_id,
            u.name as participant_name,
            ts.id as session_id,
            ts.test_type,
            ts.started_at,
            tt.id as trial_id,
            tt.trial_number,
            tt.stimulus,
            tt.response,
            tt.response_time,
            tt.correct,
            tt.created_at
        FROM test_trial tt
        JOIN test_session ts ON tt.test_session_id = ts.id
        JOIN user u ON ts.user_id = u.id
        WHERE ts.test_type = 'stroop'
        ORDER BY ts.id, tt.trial_number
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("No Stroop trials found in database.")
        return df

    # Parse JSON fields
    def parse_congruent(val):
        try:
            parsed = json.loads(val) if isinstance(val, str) else val
            return bool(parsed.get("congruent"))
        except Exception:
            return None

    def parse_word(val):
        try:
            parsed = json.loads(val) if isinstance(val, str) else val
            return parsed.get("word")
        except Exception:
            return None

    def parse_color(val):
        try:
            parsed = json.loads(val) if isinstance(val, str) else val
            return parsed.get("color")
        except Exception:
            return None

    df["congruent"] = df["stimulus"].apply(parse_congruent)
    df["stimulus_word"] = df["stimulus"].apply(parse_word)
    df["ink_color"] = df["stimulus"].apply(parse_color)
    df["rt"] = pd.to_numeric(df["response_time"], errors="coerce")
    df["correct"] = df["correct"].astype(bool)

    return df


def clean_data(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Apply behavioral reaction-time cleaning rules while preserving raw records."""
    cleaning_audit = {
        "total_raw_trials": len(raw_df),
        "error_trials_excluded_from_rt": 0,
        "anticipation_outliers_excluded": 0,
        "lapse_outliers_excluded": 0,
        "valid_rt_trials": 0,
    }

    if raw_df.empty:
        return raw_df, cleaning_audit

    # 1. Flag error trials (accuracy is calculated across all trials; RT is calculated on correct trials only)
    error_mask = ~raw_df["correct"]
    cleaning_audit["error_trials_excluded_from_rt"] = int(error_mask.sum())

    # 2. Flag implausibly fast responses (anticipation < 200 ms)
    anticipation_mask = raw_df["rt"] < RT_MIN_THRESHOLD_MS
    cleaning_audit["anticipation_outliers_excluded"] = int((raw_df["correct"] & anticipation_mask).sum())

    # 3. Flag long timeouts / attentional lapses (> 2,500 ms)
    lapse_mask = raw_df["rt"] > RT_MAX_THRESHOLD_MS
    cleaning_audit["lapse_outliers_excluded"] = int((raw_df["correct"] & lapse_mask).sum())

    # Valid mask for reaction time calculations: correct AND within physiological thresholds
    valid_rt_mask = raw_df["correct"] & (~anticipation_mask) & (~lapse_mask)
    cleaned_df = raw_df[valid_rt_mask].copy()
    cleaning_audit["valid_rt_trials"] = len(cleaned_df)

    return cleaned_df, cleaning_audit


def compute_statistics(raw_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> dict:
    """Compute overall accuracy, condition-specific reaction times, and the Stroop effect."""
    total_trials = len(raw_df)
    total_correct = int(raw_df["correct"].sum())
    accuracy = (total_correct / total_trials * 100.0) if total_trials > 0 else 0.0

    # Congruent condition (accuracy across all raw trials)
    cong_raw = raw_df[raw_df["congruent"] == True]
    cong_acc = (cong_raw["correct"].sum() / len(cong_raw) * 100.0) if len(cong_raw) > 0 else 0.0

    # Incongruent condition (accuracy across all raw trials)
    incong_raw = raw_df[raw_df["congruent"] == False]
    incong_acc = (incong_raw["correct"].sum() / len(incong_raw) * 100.0) if len(incong_raw) > 0 else 0.0

    # Reaction time metrics from cleaned trials
    mean_rt = float(cleaned_df["rt"].mean()) if not cleaned_df.empty else 0.0
    median_rt = float(cleaned_df["rt"].median()) if not cleaned_df.empty else 0.0
    std_rt = float(cleaned_df["rt"].std()) if len(cleaned_df) > 1 else 0.0

    cong_clean = cleaned_df[cleaned_df["congruent"] == True]
    incong_clean = cleaned_df[cleaned_df["congruent"] == False]

    cong_mean_rt = float(cong_clean["rt"].mean()) if not cong_clean.empty else 0.0
    cong_median_rt = float(cong_clean["rt"].median()) if not cong_clean.empty else 0.0

    incong_mean_rt = float(incong_clean["rt"].mean()) if not incong_clean.empty else 0.0
    incong_median_rt = float(incong_clean["rt"].median()) if not incong_clean.empty else 0.0

    # Stroop effect: mean incongruent RT - mean congruent RT
    stroop_effect = incong_mean_rt - cong_mean_rt

    return {
        "total_trials": total_trials,
        "total_correct": total_correct,
        "accuracy_pct": accuracy,
        "congruent_accuracy_pct": cong_acc,
        "incongruent_accuracy_pct": incong_acc,
        "overall_mean_rt": mean_rt,
        "overall_median_rt": median_rt,
        "overall_std_rt": std_rt,
        "congruent_mean_rt": cong_mean_rt,
        "congruent_median_rt": cong_median_rt,
        "incongruent_mean_rt": incong_mean_rt,
        "incongruent_median_rt": incong_median_rt,
        "stroop_effect_ms": stroop_effect,
    }


def generate_visualization(cleaned_df: pd.DataFrame, stats: dict, output_path: Path):
    """Generate a clean, publication-grade bar chart comparing Congruent vs. Incongruent RT."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)

    conditions = ["Congruent\n(Word = Color)", "Incongruent\n(Word ≠ Color)"]
    means = [stats["congruent_mean_rt"], stats["incongruent_mean_rt"]]

    cong_rts = cleaned_df[cleaned_df["congruent"] == True]["rt"]
    incong_rts = cleaned_df[cleaned_df["congruent"] == False]["rt"]

    errors = [
        cong_rts.std() if len(cong_rts) > 1 else 0.0,
        incong_rts.std() if len(incong_rts) > 1 else 0.0,
    ]

    colors = ["#2563eb", "#dc2626"]  # Blue and Red
    bars = ax.bar(conditions, means, yerr=errors, capsize=8, color=colors, alpha=0.85, width=0.45, edgecolor="#1e293b", linewidth=1.2)

    # Annotate mean values on top of bars
    for bar, mean_val in zip(bars, means):
        height = bar.get_height()
        ax.annotate(
            f"{mean_val:.1f} ms",
            xy=(bar.get_x() + bar.get_width() / 2, height / 2),
            xytext=(0, 0),
            textcoords="offset points",
            ha="center",
            va="center",
            color="white",
            fontweight="bold",
            fontsize=12,
        )

    # Title and labels
    ax.set_ylabel("Reaction Time (ms)", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Stroop Color-Word Interference Effect\nStroop Effect = {stats['stroop_effect_ms']:+.1f} ms",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    # Scientific note in caption
    fig.text(
        0.5,
        0.02,
        "Note: RT calculated from correct trials only. Error bars represent ±1 standard deviation.\n"
        "Educational behavioral experiment data; not a diagnostic instrument.",
        ha="center",
        fontsize=9,
        color="#475569",
        style="italic",
    )

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.savefig(output_path)
    plt.close()
    print(f"\nVisualization saved successfully to: {output_path}")


def main():
    print("=" * 60)
    print(" Stroop Cognitive Behavioral Experiment - Offline Analysis")
    print("=" * 60)

    raw_df = load_raw_data(DB_PATH)
    if raw_df.empty:
        print("No trial records found to analyze.")
        return

    cleaned_df, cleaning_audit = clean_data(raw_df)
    stats = compute_statistics(raw_df, cleaned_df)

    print("\n--- 1. Data Cleaning Audit ---")
    print(f"Total raw trials collected:             {cleaning_audit['total_raw_trials']}")
    print(f"Incorrect trials excluded from RT:      {cleaning_audit['error_trials_excluded_from_rt']}")
    print(f"Anticipation outliers (<200ms) dropped: {cleaning_audit['anticipation_outliers_excluded']}")
    print(f"Lapse outliers (>2500ms) dropped:       {cleaning_audit['lapse_outliers_excluded']}")
    print(f"Valid trials retained for RT analysis:  {cleaning_audit['valid_rt_trials']}")

    print("\n--- 2. Performance & Accuracy Metrics ---")
    print(f"Total Trials:              {stats['total_trials']}")
    print(f"Overall Accuracy:          {stats['accuracy_pct']:.2f}%")
    print(f"Congruent Accuracy:        {stats['congruent_accuracy_pct']:.2f}%")
    print(f"Incongruent Accuracy:      {stats['incongruent_accuracy_pct']:.2f}%")

    print("\n--- 3. Reaction Time & Stroop Effect ---")
    print(f"Overall Mean RT:           {stats['overall_mean_rt']:.2f} ms")
    print(f"Overall Median RT:         {stats['overall_median_rt']:.2f} ms")
    print(f"Overall RT Std Dev:        {stats['overall_std_rt']:.2f} ms")
    print(f"Congruent Mean RT:         {stats['congruent_mean_rt']:.2f} ms")
    print(f"Incongruent Mean RT:       {stats['incongruent_mean_rt']:.2f} ms")
    print("-" * 60)
    print(f"Calculated Stroop Effect:  {stats['stroop_effect_ms']:+.2f} ms")
    print("=" * 60)

    generate_visualization(cleaned_df, stats, OUTPUT_IMAGE)


if __name__ == "__main__":
    main()
