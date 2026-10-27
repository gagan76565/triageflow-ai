import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///tickets.db"
    ).replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024
    app.config["TRIAGEFLOW_WEBHOOK_TOKEN"] = os.environ.get(
        "TRIAGEFLOW_WEBHOOK_TOKEN", ""
    )

    db.init_app(app)

    # Import every model before create_all so new tables are registered.
    from app.models.ticket import IngestionEvent, Ticket
    from app.routes.main import main

    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

    return app
