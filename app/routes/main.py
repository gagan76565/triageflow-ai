import csv
import io

from flask import Blueprint, flash, make_response, redirect, render_template, request, url_for

from app import db
from app.ai.assigner import assign_team
from app.ai.classifier import predict_category
from app.ai.similarity import find_similar_tickets
from app.ai.urgency import detect_urgency
from app.models.ticket import Ticket

main = Blueprint("main", __name__)

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_BATCH_ROWS = 500
EMAIL_COLUMN_NAMES = {
    "email", "ticket", "ticket_text", "message", "body", "description",
    "support_email", "support_ticket", "content",
}


def analyze_and_save_ticket(email_text, include_similarity=True):
    """Run the existing triage pipeline and persist one ticket."""
    prediction = predict_category(email_text)
    category = prediction["category"]
    confidence = float(prediction["confidence"])
    urgency = detect_urgency(email_text)
    assigned_team = assign_team(category)

    similar_tickets = []
    if include_similarity:
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
    return ticket, similar_tickets


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/bulk")
def bulk_upload():
    return render_template("bulk_upload.html")


@main.route("/bulk-template.csv")
def bulk_template():
    sample_csv = (
        "\ufeffemail\r\n"
        '"Subject: Duplicate charge on invoice. I was charged twice for my subscription. Please review the duplicate payment."\r\n'
        '"The production dashboard is down and customers cannot log in. This is urgent."\r\n'
        '"How can I reset my password and enable two-factor authentication?"\r\n'
    )
    response = make_response(sample_csv)
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = 'attachment; filename="triageflow-sample-tickets.csv"'
    return response


@main.route("/bulk-analyze", methods=["POST"])
def bulk_analyze():
    uploaded_file = request.files.get("file")
    if not uploaded_file or not uploaded_file.filename:
        flash("Choose a CSV file to upload.", "error")
        return redirect(url_for("main.bulk_upload"))

    if not uploaded_file.filename.lower().endswith(".csv"):
        flash("Please upload a .csv file. Excel files can be exported as CSV first.", "error")
        return redirect(url_for("main.bulk_upload"))

    raw_data = uploaded_file.stream.read(MAX_UPLOAD_BYTES + 1)
    if len(raw_data) > MAX_UPLOAD_BYTES:
        flash("The CSV is larger than 2 MB. Split it into smaller files and try again.", "error")
        return redirect(url_for("main.bulk_upload"))

    try:
        decoded = raw_data.decode("utf-8-sig")
    except UnicodeDecodeError:
        flash("The CSV must use UTF-8 encoding. Re-save it as CSV UTF-8 and try again.", "error")
        return redirect(url_for("main.bulk_upload"))

    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames:
        flash("The CSV appears to be empty or is missing a header row.", "error")
        return redirect(url_for("main.bulk_upload"))

    normalized_headers = {
        str(header or "").strip().lower(): header
        for header in reader.fieldnames
    }
    email_header = next(
        (normalized_headers[name] for name in EMAIL_COLUMN_NAMES if name in normalized_headers),
        None,
    )
    if email_header is None:
        flash(
            "Could not find a ticket text column. Use a header such as email, ticket, message, body, or description.",
            "error",
        )
        return redirect(url_for("main.bulk_upload"))

    rows = list(reader)
    if len(rows) > MAX_BATCH_ROWS:
        flash(f"A batch can contain at most {MAX_BATCH_ROWS} rows. Split this file and upload it again.", "error")
        return redirect(url_for("main.bulk_upload"))

    skip_duplicates = request.form.get("skip_duplicates") == "on"
    seen_in_upload = set()
    report_rows = []
    imported_tickets = []
    failed_count = 0
    skipped_count = 0

    for row_number, row in enumerate(rows, start=2):
        email_text = str(row.get(email_header) or "").strip()
        if not email_text:
            report_rows.append({
                "row_number": row_number,
                "email": "",
                "category": "—",
                "confidence": None,
                "urgency": "—",
                "assigned_team": "—",
                "status": "Skipped: empty ticket",
                "ticket_id": None,
            })
            skipped_count += 1
            continue

        exact_key = email_text.casefold()
        if skip_duplicates and exact_key in seen_in_upload:
            report_rows.append({
                "row_number": row_number,
                "email": email_text,
                "category": "—",
                "confidence": None,
                "urgency": "—",
                "assigned_team": "—",
                "status": "Skipped: duplicate in file",
                "ticket_id": None,
            })
            skipped_count += 1
            continue
        seen_in_upload.add(exact_key)

        if skip_duplicates:
            existing = Ticket.query.filter_by(email=email_text).first()
            if existing:
                report_rows.append({
                    "row_number": row_number,
                    "email": email_text,
                    "category": existing.category,
                    "confidence": existing.confidence,
                    "urgency": existing.urgency,
                    "assigned_team": existing.assigned_team,
                    "status": "Skipped: already in system",
                    "ticket_id": existing.id,
                })
                skipped_count += 1
                continue

        try:
            ticket, _similar_tickets = analyze_and_save_ticket(email_text, include_similarity=False)
            imported_tickets.append(ticket)
            report_rows.append({
                "row_number": row_number,
                "email": email_text,
                "category": ticket.category,
                "confidence": ticket.confidence,
                "urgency": ticket.urgency,
                "assigned_team": ticket.assigned_team,
                "status": "Analyzed",
                "ticket_id": None,
            })
        except Exception:
            failed_count += 1
            report_rows.append({
                "row_number": row_number,
                "email": email_text,
                "category": "—",
                "confidence": None,
                "urgency": "—",
                "assigned_team": "—",
                "status": "Failed to analyze",
                "ticket_id": None,
            })

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("The batch could not be saved. No tickets from this batch were committed; please retry.", "error")
        return redirect(url_for("main.bulk_upload"))

    imported_iter = iter(imported_tickets)
    for report_row in report_rows:
        if report_row["status"] == "Analyzed":
            report_row["ticket_id"] = next(imported_iter).id

    return render_template(
        "bulk_report.html",
        report_rows=report_rows,
        total_rows=len(rows),
        imported_count=len(imported_tickets),
        skipped_count=skipped_count,
        failed_count=failed_count,
    )


@main.route("/bulk-report.csv", methods=["POST"])
def download_bulk_report():
    raw_ids = request.form.getlist("ticket_ids")
    ids = []
    for value in raw_ids:
        try:
            ticket_id = int(value)
            if ticket_id > 0:
                ids.append(ticket_id)
        except (TypeError, ValueError):
            continue

    tickets = Ticket.query.filter(Ticket.id.in_(set(ids))).order_by(Ticket.id.asc()).all() if ids else []
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ticket_id", "email", "category", "confidence_percent", "urgency", "assigned_team", "status", "created_at"])
    for ticket in tickets:
        writer.writerow([
            ticket.id, ticket.email, ticket.category, ticket.confidence,
            ticket.urgency, ticket.assigned_team, ticket.status,
            ticket.created_at.isoformat() if ticket.created_at else "",
        ])

    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = 'attachment; filename="triageflow-batch-report.csv"'
    return response


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
        "Billing", "Bug Report", "Feature Request",
        "Account Access", "How-To Question", "General Inquiry",
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

    ticket, similar_tickets = analyze_and_save_ticket(email_text)
    db.session.commit()

    ai_warning = (
        "Low AI confidence. Manual review is recommended."
        if ticket.confidence < 50
        else None
    )
    result = {
        "email": email_text,
        "category": ticket.category,
        "confidence": ticket.confidence,
        "urgency": ticket.urgency,
        "assigned_team": ticket.assigned_team,
        "similar_tickets": similar_tickets,
        "ai_warning": ai_warning,
        "ticket_id": ticket.id,
    }
    return render_template("result.html", result=result)
