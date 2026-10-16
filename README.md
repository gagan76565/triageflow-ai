# TriageFlow AI — Support Ticket Classification & Routing

A Flask web app that helps organize incoming support messages. It classifies a ticket, estimates urgency, suggests a team, checks for similar existing tickets, and stores results for dashboard review.

**Live app:** https://triageflow-ai.onrender.com  
**Repository:** https://github.com/gagan76565/triageflow-ai

## Features

- Predicts a support-ticket category with a saved scikit-learn model.
- Reports the model's top class score as a confidence percentage.
- Estimates urgency using transparent keyword rules (Critical, High, Medium, Low).
- Maps categories to suggested teams such as Engineering, Finance, Support, Product, and Customer Success.
- Finds similar existing ticket text using TF-IDF and cosine similarity.
- Persists tickets in SQLite through Flask-SQLAlchemy.
- Dashboard filters for search, urgency, and ticket status, along with category and urgency counts.
- Ticket-detail view and a POST action to mark a ticket as resolved.
- Displays a manual-review warning when classifier confidence is below 50%.

## Tech stack

- Python and Flask
- scikit-learn and joblib for the saved text-classification model
- TF-IDF and cosine similarity for similar-ticket lookup
- Flask-SQLAlchemy and SQLite for storage
- Jinja templates, HTML, CSS, and JavaScript
- Gunicorn for the Render deployment

## How the workflow works

1. Enter a support email/message in the web interface.
2. The saved classifier predicts a category and confidence score.
3. Keyword rules estimate urgency and a mapping suggests a team.
4. Existing ticket text is compared with TF-IDF vectors; matches above the configured similarity threshold are surfaced.
5. The ticket is saved and can be reviewed, filtered, and marked as resolved in the dashboard.

## Run locally

Requirements: Python 3.10 or newer is recommended.

```bash
git clone https://github.com/gagan76565/triageflow-ai.git
cd triageflow-ai
python -m venv .venv
```

Activate the virtual environment:

**Windows PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

Install dependencies and start the app:

```bash
python -m pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:5000.

## Deployment

The repository includes a `Procfile` configured for Gunicorn. The deployed app runs on Render:

https://triageflow-ai.onrender.com

## Notes and limitations

- The urgency estimate is keyword-based, not a trained urgency classifier.
- A confidence score is the model's score for its chosen category; it should not be interpreted as a calibrated probability of correctness.
- Similar-ticket lookup compares text similarity, not semantic equivalence.
- The application has no user authentication in the current implementation. Do not expose sensitive support messages without adding appropriate access controls and privacy safeguards.
- Tickets are stored in SQLite; confirm the deployment's storage configuration before relying on persistence across instance replacement or restart.

## Author

**Gagan** — https://github.com/gagan76565
