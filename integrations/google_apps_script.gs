/**
 * TriageFlow AI Google Sheets connector.
 *
 * Setup:
 * 1. Open the Google Form's linked response spreadsheet.
 * 2. Extensions -> Apps Script; paste this file.
 * 3. Project Settings -> Script Properties:
 *    TRIAGEFLOW_API_URL = https://triageflow-ai.onrender.com/api/integrations/google-sheets/tickets
 *    TRIAGEFLOW_WEBHOOK_TOKEN = the same secret configured on Render
 *    TICKET_TEXT_COLUMN = optional exact header name containing the support message
 * 4. Add a trigger for onFormSubmit, event source "From spreadsheet",
 *    event type "On form submit".
 */

function onFormSubmit(e) {
  if (!e || !e.range || !e.source) {
    throw new Error("Use an installable spreadsheet 'On form submit' trigger.");
  }

  const properties = PropertiesService.getScriptProperties();
  const endpoint = properties.getProperty("TRIAGEFLOW_API_URL");
  const token = properties.getProperty("TRIAGEFLOW_WEBHOOK_TOKEN");

  if (!endpoint || !token) {
    throw new Error("Set TRIAGEFLOW_API_URL and TRIAGEFLOW_WEBHOOK_TOKEN in Script Properties.");
  }

  const sheet = e.range.getSheet();
  const rowNumber = e.range.getRow();
  const lastColumn = sheet.getLastColumn();
  const headers = sheet.getRange(1, 1, 1, lastColumn).getDisplayValues()[0];
  const values = sheet.getRange(rowNumber, 1, 1, lastColumn).getDisplayValues()[0];

  const row = {};
  headers.forEach(function (header, index) {
    const key = String(header || "").trim();
    if (key) row[key] = String(values[index] || "").trim();
  });

  const message = chooseTicketText_(row, properties.getProperty("TICKET_TEXT_COLUMN"));
  if (!message) {
    throw new Error("No support message found in this response row. Configure TICKET_TEXT_COLUMN.");
  }

  // Stable per spreadsheet, sheet, and row. Backend rejects duplicate processing safely.
  const sourceId = e.source.getId() + ":" + sheet.getSheetId() + ":" + rowNumber;
  const payload = {
    source_id: sourceId,
    source_name: sheet.getName(),
    email: message
  };

  const options = {
    method: "post",
    contentType: "application/json",
    headers: { "X-Webhook-Token": token },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  let lastError = "";
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const response = UrlFetchApp.fetch(endpoint, options);
      const status = response.getResponseCode();
      if (status >= 200 && status < 300) return;

      lastError = "TriageFlow returned HTTP " + status + ": " + response.getContentText();
      if (status < 500 && status !== 429) {
        throw new Error(lastError);
      }
    } catch (error) {
      lastError = String(error);
      if (attempt === 2) break;
    }

    Utilities.sleep(Math.pow(2, attempt) * 1000);
  }

  throw new Error("TriageFlow ingestion failed after retries: " + lastError);
}


function chooseTicketText_(row, configuredHeader) {
  const keys = Object.keys(row);
  if (configuredHeader) {
    const match = keys.find(function (key) {
      return key.toLowerCase() === configuredHeader.trim().toLowerCase();
    });
    if (!match || !row[match]) {
      throw new Error("Configured TICKET_TEXT_COLUMN was not found or is empty: " + configuredHeader);
    }
    return row[match];
  }

  const preferred = [
    "support email", "ticket", "ticket text", "message", "description",
    "issue", "how can we help", "how can we help you", "request", "details"
  ];
  for (let i = 0; i < preferred.length; i++) {
    const match = keys.find(function (key) {
      return key.toLowerCase() === preferred[i];
    });
    if (match && row[match]) return row[match];
  }

  // Fallback: include non-empty response fields except common metadata columns.
  const ignored = ["timestamp", "time stamp", "email address", "name", "phone", "phone number"];
  return keys
    .filter(function (key) {
      return row[key] && ignored.indexOf(key.toLowerCase()) === -1;
    })
    .map(function (key) {
      return key + ": " + row[key];
    })
    .join("\n");
}
