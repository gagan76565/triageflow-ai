from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.ai.assigner import assign_team
from app.ai.classifier import predict_category
from app.ai.similarity import find_similar_tickets
from app.ai.urgency import detect_urgency
from app.models.ticket import Ticket

main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/dashboard")
def dashboard():
    search = request.args.get("search", "").strip()
    urgency_filter = request.args.get("urgency", "").strip()
    status_filter = request.args.get("status", "").strip()

    query = Ticket.query

    if search:
        query = query.filter(Ticket.email.ilike(f"%{search}%"))

    if urgency_filter in {"Critical", "High", "Medium", "Low"}:
        query = query.filter_by(urgency=urgency_filter)

    if status_filter in {"Open", "Resolved"}:
        query = query.filter_by(status=status_filter)

    tickets = query.order_by(Ticket.created_at.desc()).all()

    total_tickets = Ticket.query.count()
    critical_tickets = Ticket.query.filter_by(urgency="Critical").count()
    resolved_tickets = Ticket.query.filter_by(status="Resolved").count()

    categories = [
        "Billing",
        "Bug Report",
        "Feature Request",
        "Account Access",
        "How-To Question",
        "General Inquiry",
    ]
    urgency_levels = ["Critical", "High", "Medium", "Low"]

    category_counts = [
        Ticket.query.filter_by(category=category).count()
        for category in categories
    ]
    urgency_counts = [
        Ticket.query.filter_by(urgency=level).count()
        for level in urgency_levels
    ]

    return render_template(
        "dashboard.html",
        tickets=tickets,
        total_tickets=total_tickets,
        critical_tickets=critical_tickets,
        resolved_tickets=resolved_tickets,
        categories=categories,
        category_counts=category_counts,
        urgency_levels=urgency_levels,
        urgency_counts=urgency_counts,
        search=search,
        urgency_filter=urgency_filter,
        status_filter=status_filter,
    )


@main.route("/tickets/<int:ticket_id>")
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    return render_template("ticket_detail.html", ticket=ticket)


@main.route("/tickets/<int:ticket_id>/resolve", methods=["POST"])
def resolve_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.status != "Resolved":
        ticket.status = "Resolved"
        db.session.commit()
        flash(f"Ticket #{ticket.id} marked as resolved.", "success")
    else:
        flash(f"Ticket #{ticket.id} is already resolved.", "info")

    return redirect(url_for("main.ticket_detail", ticket_id=ticket.id))


@main.route("/analyze", methods=["POST"])
def analyze():
    email_text = request.form.get("email", "").strip()

    if not email_text:
        flash("Please enter a support email before analyzing.", "error")
        return redirect(url_for("main.home") + "#new-ticket")

    prediction = predict_category(email_text)
    category = prediction["category"]
    confidence = float(prediction["confidence"])
    urgency = detect_urgency(email_text)
    assigned_team = assign_team(category)

    existing_ticket_texts = [ticket.email for ticket in Ticket.query.all()]
    similar_tickets = find_similar_tickets(email_text, existing_ticket_texts)

    ticket = Ticket(
        email=email_text,
        category=category,
        confidence=confidence,
        urgency=urgency,
        assigned_team=assigned_team,
    )
    db.session.add(ticket)
    db.session.commit()

    ai_warning = (
        "Low AI confidence. Manual review is recommended."
        if confidence < 50
        else None
    )

    result = {
        "email": email_text,
        "category": category,
        "confidence": confidence,
        "urgency": urgency,
        "assigned_team": assigned_team,
        "similar_tickets": similar_tickets,
        "ai_warning": ai_warning,
        "ticket_id": ticket.id,
    }
    return render_template("result.html", result=result)
