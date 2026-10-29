"""Application launcher script.

Run with:
    python run.py
or:
    python app.py
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
