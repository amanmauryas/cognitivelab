from pathlib import Path

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Initialise SQLAlchemy and create missing tables without altering existing ones."""
    data_dir = Path(app.instance_path).parent / "data"
    data_dir.mkdir(exist_ok=True)
    db.init_app(app)
    with app.app_context():
        db.create_all()
