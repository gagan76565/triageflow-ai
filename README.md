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

## Bulk ticket analysis

Use **Bulk Analyze** in the header to upload a UTF-8 CSV file containing up to 500 tickets (maximum 2 MB). The file must include a ticket-text column named `email`, `ticket`, `ticket_text`, `message`, `body`, `description`, `support_email`, `support_ticket`, or `content`. Other columns are ignored in this version.

- Validates file type, size, encoding, headers, and row count.
- Runs the same category, urgency, and team-routing pipeline used by single-ticket analysis.
- Optionally skips exact duplicate ticket text already in the database or repeated within the uploaded file.
- Shows analyzed, skipped, and failed rows in a batch report.
- Exports successfully analyzed tickets as CSV.

Download a sample file from the Bulk Analyze page. Excel files should be exported as CSV UTF-8 before upload.

## Automatic Google Forms / Google Sheets ingestion

The repository includes an authenticated webhook and a Google Apps Script connector at `integrations/google_apps_script.gs`. When an installable spreadsheet **On form submit** trigger runs, the script sends the new response row to TriageFlow AI. A stable spreadsheet/sheet/row identifier prevents retries from creating the same ticket twice.

### Configure Render

Set these environment variables in the Render service:

- `SECRET_KEY`: a long, random value used to sign Flask sessions.
- `TRIAGEFLOW_WEBHOOK_TOKEN`: a long, random shared secret. Do not commit this value to GitHub.
- `DATABASE_URL` (recommended for durable deployment): a PostgreSQL connection URL. If unset, the app uses SQLite.

The webhook endpoint is:

```text
POST https://triageflow-ai.onrender.com/api/integrations/google-sheets/tickets
Header: X-Webhook-Token: <your shared secret>
Content-Type: application/json

{
  "source_id": "spreadsheet-id:sheet-id:row-number",
  "source_name": "Form Responses 1",
  "email": "The support request text"
}
```

### Configure Google Apps Script

1. Open the spreadsheet linked to the Google Form.
2. Select **Extensions → Apps Script** and paste the contents of `integrations/google_apps_script.gs`.
3. Open **Project Settings → Script Properties** and set:
   - `TRIAGEFLOW_API_URL` = `https://triageflow-ai.onrender.com/api/integrations/google-sheets/tickets`
   - `TRIAGEFLOW_WEBHOOK_TOKEN` = the exact same secret set on Render
   - `TICKET_TEXT_COLUMN` = optional, the exact response-sheet header containing the support message
4. In Apps Script, add an installable trigger for `onFormSubmit`, event source **From spreadsheet**, event type **On form submit**.
5. Submit a test Google Form response and verify the resulting ticket appears in the TriageFlow AI dashboard.

The first trigger setup requires authorization from the Google account owner. The webhook rejects requests without the configured secret and safely returns the existing ticket for a repeated source row.

## Deployment and data durability

The app calls `db.create_all()` at startup, which creates the new ingestion-events table without modifying existing ticket columns. For production use, configure a persistent PostgreSQL database through `DATABASE_URL`; SQLite on an ephemeral host may lose data when the instance is replaced. Do not connect sensitive customer data until authentication, access controls, retention, and privacy requirements are addressed.
