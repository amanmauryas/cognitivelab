"""Stroop task scoring and statistical calculations.

Provides pure Python helper functions for calculating performance metrics,
reaction time statistics, and cognitive interference (Stroop effect).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List


def compute_stroop_metrics(trials: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate descriptive statistics and Stroop interference from trial dictionaries.

    Args:
        trials: List of trial dictionaries with 'correct', 'rt', and 'congruent' keys.

    Returns:
        Dictionary containing overall accuracy, reaction time metrics,
        condition splits (congruent vs incongruent), and the Stroop effect (in ms).
    """
    if not trials:
        return {
            "total_trials": 0,
            "accuracy": 0.0,
            "error_rate": 0.0,
            "mean_rt": 0.0,
            "median_rt": 0.0,
            "std_rt": 0.0,
            "congruent_accuracy": 0.0,
            "incongruent_accuracy": 0.0,
            "congruent_mean_rt": 0.0,
            "incongruent_mean_rt": 0.0,
            "accuracy_interference": 0.0,
            "stroop_effect": 0.0,
        }

    total_trials = len(trials)
    correct_trials = [t for t in trials if t.get("correct")]
    total_correct = len(correct_trials)
    accuracy = (total_correct / total_trials) * 100.0
    error_rate = 100.0 - accuracy

    # RT calculations are performed on correct trials only (standard psychometric practice)
    correct_rts = sorted([float(t.get("rt", 0)) for t in correct_trials])
    num_correct_rts = len(correct_rts)

    if num_correct_rts > 0:
        mean_rt = sum(correct_rts) / num_correct_rts
        if num_correct_rts % 2 != 0:
            median_rt = correct_rts[num_correct_rts // 2]
        else:
            median_rt = (correct_rts[num_correct_rts // 2 - 1] + correct_rts[num_correct_rts // 2]) / 2.0

        if num_correct_rts > 1:
            variance = sum((rt - mean_rt) ** 2 for rt in correct_rts) / (num_correct_rts - 1)
            std_rt = math.sqrt(variance)
        else:
            std_rt = 0.0
    else:
        mean_rt = 0.0
        median_rt = 0.0
        std_rt = 0.0

    # Congruent condition
    congruent_trials = [t for t in trials if t.get("congruent")]
    cong_correct = [t for t in congruent_trials if t.get("correct")]
    cong_accuracy = (len(cong_correct) / len(congruent_trials) * 100.0) if congruent_trials else 0.0
    cong_mean_rt = (sum(float(t.get("rt", 0)) for t in cong_correct) / len(cong_correct)) if cong_correct else 0.0

    # Incongruent condition
    incongruent_trials = [t for t in trials if not t.get("congruent")]
    incong_correct = [t for t in incongruent_trials if t.get("correct")]
    incong_accuracy = (len(incong_correct) / len(incongruent_trials) * 100.0) if incongruent_trials else 0.0
    incong_mean_rt = (sum(float(t.get("rt", 0)) for t in incong_correct) / len(incong_correct)) if incong_correct else 0.0

    # Stroop Interference: positive indicates slower reaction time during conflict
    stroop_effect = incong_mean_rt - cong_mean_rt
    accuracy_interference = cong_accuracy - incong_accuracy

    return {
        "total_trials": total_trials,
        "accuracy": round(accuracy, 2),
        "error_rate": round(error_rate, 2),
        "mean_rt": round(mean_rt, 2),
        "median_rt": round(median_rt, 2),
        "std_rt": round(std_rt, 2),
        "congruent_accuracy": round(cong_accuracy, 2),
        "incongruent_accuracy": round(incong_accuracy, 2),
        "congruent_mean_rt": round(cong_mean_rt, 2),
        "incongruent_mean_rt": round(incong_mean_rt, 2),
        "accuracy_interference": round(accuracy_interference, 2),
        "stroop_effect": round(stroop_effect, 2),
    }
