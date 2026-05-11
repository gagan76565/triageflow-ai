from flask import (
    Blueprint,
    render_template,
    request,
    redirect
)

from app.ai.classifier import predict_category
from app.ai.urgency import detect_urgency
from app.ai.assigner import assign_team
from app.ai.similarity import find_similar_tickets

from app.models.ticket import Ticket
from app import db

main = Blueprint("main", __name__)

@main.route("/")
def home():

    return render_template("index.html")


@main.route("/dashboard")
@main.route("/dashboard")
def dashboard():

    search = request.args.get("search", "")

    urgency_filter = request.args.get("urgency", "")

    query = Ticket.query

    # Search filter
    if search:

        query = query.filter(
            Ticket.email.contains(search)
        )

    # Urgency filter
    if urgency_filter:

        query = query.filter_by(
            urgency=urgency_filter
        )

    tickets = query.order_by(
        Ticket.created_at.desc()
    ).all()

    total_tickets = Ticket.query.count()

    critical_tickets = Ticket.query.filter_by(
        urgency="Critical"
    ).count()

    resolved_tickets = Ticket.query.filter_by(
        status="Resolved"
    ).count()

    # Category analytics
    categories = [
        "Billing",
        "Bug Report",
        "Feature Request",
        "Account Access",
        "How-To Question",
        "General Inquiry"
    ]

    category_counts = []

    for category in categories:

        count = Ticket.query.filter_by(
            category=category
        ).count()

        category_counts.append(count)

    # Urgency analytics
    urgency_levels = [
        "Critical",
        "High",
        "Medium",
        "Low"
    ]

    urgency_counts = []

    for level in urgency_levels:

        count = Ticket.query.filter_by(
            urgency=level
        ).count()

        urgency_counts.append(count)

    return render_template(
        "dashboard.html",
        tickets=tickets,
        total_tickets=total_tickets,
        critical_tickets=critical_tickets,
        resolved_tickets=resolved_tickets,
        categories=categories,
        category_counts=category_counts,
        urgency_levels=urgency_levels,
        urgency_counts=urgency_counts
    )

@main.route("/update-status/<int:ticket_id>")
def update_status(ticket_id):

    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.status == "Open":
        ticket.status = "Resolved"

    else:
        ticket.status = "Open"

    db.session.commit()

    return redirect("/dashboard")


@main.route("/analyze", methods=["POST"])
def analyze():

    email_text = request.form.get("email")

    prediction = predict_category(email_text)

    category = prediction["category"]

    confidence = prediction["confidence"]
    # Confidence warning system
    if confidence < 50:

        ai_warning = (
            "Low AI confidence. "
            "Manual review recommended."
        )

    else:

        ai_warning = None
    
    urgency = detect_urgency(email_text)

    assigned_team = assign_team(category)

    # Duplicate ticket detection
    existing_ticket_texts = [
        t.email for t in Ticket.query.all()
    ]

    similar_tickets = find_similar_tickets(
        email_text,
        existing_ticket_texts
    )

    # Save ticket
    ticket = Ticket(
        email=email_text,
        category=category,
        confidence=confidence,
        urgency=urgency,
        assigned_team=assigned_team
    )

    db.session.add(ticket)

    db.session.commit()

    result = {
        "email": email_text,
        "category": category,
        "confidence": confidence,
        "urgency": urgency,
        "assigned_team": assigned_team,
        "similar_tickets": similar_tickets,
        "ai_warning": ai_warning
    }

    return render_template(
        "result.html",
        result=result
    )