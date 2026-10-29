"""Single source of truth for tools exposed by the clinical workspace.

Add a new cognitive task or diagnostic scale here before implementing its blueprint.
The workspace and dashboards read this registry, keeping discovery separate from each
tool's experiment or scoring code.
"""

COGNITIVE_TASKS = (
    {
        "id": "stroop",
        "name": "Stroop Color-Word Task",
        "category": "Inhibition",
        "description": "Measures colour-word interference, response accuracy, and reaction time.",
        "endpoint": "stroop.test",
        "status": "available",
    },
    {
        "id": "n_back",
        "name": "N-Back Task",
        "category": "Working memory",
        "description": "Planned working-memory task.",
        "endpoint": None,
        "status": "planned",
    },
    {
        "id": "flanker",
        "name": "Flanker Task",
        "category": "Attention",
        "description": "Planned selective-attention task.",
        "endpoint": None,
        "status": "planned",
    },
)

DIAGNOSTIC_SCALES = (
    {
        "id": "phq9",
        "name": "PHQ-9",
        "category": "Depression symptoms",
        "description": "Patient Health Questionnaire (9-item) for screening and severity of depressive symptoms.",
        "status": "available",
    },
    {
        "id": "gad7",
        "name": "GAD-7",
        "category": "Anxiety symptoms",
        "description": "Generalized Anxiety Disorder 7-item scale assessing symptom frequency and severity.",
        "status": "available",
    },
    {
        "id": "ybocs",
        "name": "Y-BOCS",
        "category": "Obsessive-compulsive symptoms",
        "description": "Yale-Brown Obsessive Compulsive Scale assessing obsession and compulsion severity.",
        "status": "available",
    },
)

WORKSHEETS = (
    ("thought_record", "Interactive Thought Record"),
    ("daily_diary", "Daily Diary Card"),
    ("behavioral_chain", "Behavioral Chain Analysis"),
)


def available_task(task_id: str):
    return next((task for task in COGNITIVE_TASKS if task["id"] == task_id), None)
