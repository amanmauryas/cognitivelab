from datetime import datetime


def generate_participant_id(name: str, gender: str, monthly_count: int) -> str:
    """Generate the existing participant-ID format without querying the database."""
    name_initial = name.strip()[:1].upper()
    gender_initial = gender.strip()[:1].upper()
    date_code = datetime.now().strftime("%y%m")
    return f"{name_initial}{gender_initial}{date_code}{monthly_count + 1:04d}"
