import os
from src import create_app, db


app = create_app(os.getenv("AWARDS_CONFIG") or "default")


@app.cli.command("init_app")
def setup_app():
    db.create_all()
    try:
        from src.email_list import insert_employees
        insert_employees()
    except ImportError:
        print("Not development env")
