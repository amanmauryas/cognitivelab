"""Small shared helpers for the existing session-based authentication flow."""


def normalize_username(username: str) -> str:
    return username.strip().lower()


def is_patient_role(role: str | None) -> bool:
    """Keep access compatible with legacy accounts stored as `user`."""
    return role in {"patient", "user"}
