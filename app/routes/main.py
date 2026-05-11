from flask import Blueprint, render_template, request

from app.ai.classifier import predict_category
from app.ai.urgency import detect_urgency
from app.ai.assigner import assign_team

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return render_template("index.html")

@main.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@main.route("/analyze", methods=["POST"])
def analyze():

    email_text = request.form.get("email")

    prediction = predict_category(email_text)

    category = prediction["category"]

    confidence = prediction["confidence"]

    urgency = detect_urgency(email_text)

    assigned_team = assign_team(category)

    result = {
        "email": email_text,
        "category": category,
        "confidence": confidence,
        "urgency": urgency,
        "assigned_team": assigned_team
    }

    return render_template(
        "result.html",
        result=result
    )