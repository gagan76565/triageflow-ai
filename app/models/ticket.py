from datetime import datetime

from app import db

class Ticket(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.Text, nullable=False)

    category = db.Column(db.String(100), nullable=False)

    confidence = db.Column(db.Float, nullable=False)

    urgency = db.Column(db.String(50), nullable=False)

    assigned_team = db.Column(db.String(100), nullable=False)

    status = db.Column(
        db.String(50),
        default="Open"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )