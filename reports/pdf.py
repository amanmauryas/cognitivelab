"""Reporting and export utilities for cognitive and diagnostic sessions.

Provides generic plain text, CSV, and printable HTML summary generators.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any, Dict, List


def generate_session_summary_text(session: Dict[str, Any], user: Dict[str, Any]) -> str:
    """Generate a clean, structured plain text summary report of a test session."""
    metrics = session.get("summary_metrics") or {}
    completed = session.get("completed_at")
    date_str = completed.strftime("%Y-%m-%d %H:%M UTC") if isinstance(completed, datetime) else str(completed)

    lines = [
        "=" * 60,
        f" COGNITIVE LAB - SESSION SUMMARY REPORT",
        "=" * 60,
        f"Participant ID:  {user.get('participant_id', 'N/A')}",
        f"Participant:     {user.get('name', 'N/A')} ({user.get('username', 'N/A')})",
        f"Age / Gender:    {user.get('age', 'N/A')} / {user.get('gender', 'N/A')}",
        f"Task Type:       {session.get('test_type', 'N/A').title()}",
        f"Completed:       {date_str}",
        "-" * 60,
        " PERFORMANCE METRICS:",
        f"  Total Trials:          {session.get('total_trials', 0)}",
        f"  Overall Accuracy:      {metrics.get('accuracy', 0):.1f}%",
        f"  Error Rate:            {metrics.get('error_rate', 0):.1f}%",
        f"  Mean Reaction Time:    {metrics.get('mean_rt', 0):.1f} ms",
        f"  Median Reaction Time:  {metrics.get('median_rt', 0):.1f} ms",
        f"  RT Variability (SD):   {metrics.get('std_rt', 0):.1f} ms",
        "-" * 60,
        " CONDITION BREAKDOWN:",
        f"  Congruent Accuracy:    {metrics.get('congruent_accuracy', 0):.1f}%",
        f"  Incongruent Accuracy:  {metrics.get('incongruent_accuracy', 0):.1f}%",
        f"  Congruent Mean RT:     {metrics.get('congruent_mean_rt', 0):.1f} ms",
        f"  Incongruent Mean RT:   {metrics.get('incongruent_mean_rt', 0):.1f} ms",
        f"  Stroop Effect:         {metrics.get('stroop_effect', 0):+.1f} ms",
        "=" * 60,
        " NOTICE: For educational and behavioral research modeling only.",
        " This document does not constitute a medical or clinical diagnosis.",
        "=" * 60,
    ]
    return "\n".join(lines)


def export_trials_csv(trials: List[Dict[str, Any]]) -> str:
    """Export a list of trial records into CSV format."""
    output = io.StringIO()
    fieldnames = [
        "trial_number",
        "word",
        "color",
        "congruent",
        "response",
        "correct",
        "reaction_time_ms",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for t in trials:
        stimulus = t.get("stimulus") or {}
        resp = t.get("response") or {}
        writer.writerow({
            "trial_number": t.get("trial_number"),
            "word": stimulus.get("word"),
            "color": stimulus.get("color"),
            "congruent": stimulus.get("congruent"),
            "response": resp.get("selected_color"),
            "correct": t.get("correct"),
            "reaction_time_ms": t.get("response_time"),
        })

    return output.getvalue()
