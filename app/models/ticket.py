from datetime import datetime

from app import db


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    urgency = db.Column(db.String(50), nullable=False)
    assigned_team = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default="Open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class IngestionEvent(db.Model):
    """Idempotency record for external ticket sources such as Google Sheets."""

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    source_name = db.Column(db.String(120), nullable=False, default="google_sheets")
    ticket_id = db.Column(db.Integer, db.ForeignKey("ticket.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
