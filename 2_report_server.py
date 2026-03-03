"""
STEP 3 — Receive interview report → Write to Google Sheet → Send outcome email
Deploy this on Railway or Render (free tier) as a Flask webhook.
"""

from flask import Flask, request, jsonify
import os, json, base64, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

app = Flask(__name__)

SHEET_ID = "1z5xTC1IpUorw8Iqlc4avNNm8ujAYWAu83JvDToskXVo"
YOUR_EMAIL = "shashanksharma0295@gmail.com"
SHORTLIST_THRESHOLD = 8

REPORT_HEADERS = [
    "Timestamp", "Candidate Name", "Email", "Resume",
    "Job Fit Score", "Verdict", "Cheating Flag", "Cheating Reason",
    "Accuracy Score", "Communication Score", "Confidence Score",
    "Strengths", "Weaknesses", "Opportunities", "Threats",
    "Summary", "Recommendation", "Tab Switches",
    "Q1 Answer", "Q2 Answer", "Q3 Answer"
]

def get_services():
    """Load Google credentials from environment variable (set on Railway/Render)"""
    token_data = os.environ.get("GOOGLE_TOKEN_JSON")
    creds = Credentials.from_authorized_user_info(json.loads(token_data))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    gmail = build("gmail", "v1", credentials=creds)
    sheets = build("sheets", "v4", credentials=creds)
    return gmail, sheets

def ensure_report_sheet(sheets):
    """Create Report tab with headers if it doesn't exist"""
    try:
        sheets.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range="Reports!A1"
        ).execute()
    except:
        # Sheet doesn't exist, create it and add headers
        sheets.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": [{"addSheet": {"properties": {"title": "Reports"}}}]}
        ).execute()
        sheets.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range="Reports!A1",
            valueInputOption="RAW",
            body={"values": [REPORT_HEADERS]}
        ).execute()

def write_report_to_sheet(sheets, data, report):
    answers = data.get("answers", [{}, {}, {}])
    row = [
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get("candidate_name", ""),
        data.get("candidate_email", ""),
        data.get("resume", ""),
        report.get("job_fit_score", ""),
        report.get("verdict", ""),
        report.get("cheating_flag", ""),
        report.get("cheating_reason", ""),
        report.get("accuracy_score", ""),
        report.get("communication_score", ""),
        report.get("confidence_score", ""),
        " | ".join(report.get("strengths", [])),
        " | ".join(report.get("weaknesses", [])),
        " | ".join(report.get("opportunities", [])),
        " | ".join(report.get("threats", [])),
        report.get("summary", ""),
        report.get("recommendation", ""),
        data.get("tab_switches", 0),
        answers[0].get("answer", "") if len(answers) > 0 else "",
        answers[1].get("answer", "") if len(answers) > 1 else "",
        answers[2].get("answer", "") if len(answers) > 2 else "",
    ]
    sheets.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range="Reports!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]}
    ).execute()

def send_outcome_email(gmail, candidate_name, candidate_email, verdict, score):
    first = candidate_name.split()[0]
    is_shortlisted = verdict.lower() == "shortlisted"

    if is_shortlisted:
        subject = "Update on Your Application — Sportskeeda APM Role"
        html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  body{{font-family:'Helvetica Neue',Arial,sans-serif;background:#f5f5f5;margin:0;padding:0}}
  .w{{max-width:600px;margin:40px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08)}}
  .h{{background:#1a1a2e;padding:28px 40px}}.h h1{{color:#fff;font-size:20px;font-weight:700;margin:0}}
  .h p{{color:#8888aa;font-size:13px;margin:4px 0 0}}
  .b{{padding:32px 40px;color:#333;line-height:1.7;font-size:15px}}
  .b p{{margin:0 0 16px}}
  .box{{background:#f0fff8;border-left:4px solid #00d4aa;padding:14px 20px;border-radius:4px;margin:20px 0;font-size:14px}}
  .f{{background:#f9f9f9;padding:16px 40px;border-top:1px solid #eee;font-size:12px;color:#aaa}}
</style></head><body>
<div class="w">
  <div class="h"><h1>Sportskeeda</h1><p>Application Update</p></div>
  <div class="b">
    <p>Hi {first},</p>
    <p>Thank you for taking the time to complete your interview for the <strong>Associate Product Manager</strong> role at Sportskeeda.</p>
    <p>We're pleased to let you know that you've been <strong>shortlisted</strong> for the next stage of our hiring process. Our team was impressed with your responses and we'd love to continue the conversation.</p>
    <div class="box">📩 Someone from our team will reach out to you shortly with details about the next steps.</div>
    <p>In the meantime, if you have any questions, feel free to reply to this email.</p>
    <p>Looking forward to speaking with you soon.</p>
    <p>Warm regards,<br><strong>Talent Team</strong><br>Sportskeeda</p>
  </div>
  <div class="f">This is an automated message from Sportskeeda's hiring system.</div>
</div></body></html>"""
    else:
        subject = "Your Application at Sportskeeda — Associate Product Manager"
        html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  body{{font-family:'Helvetica Neue',Arial,sans-serif;background:#f5f5f5;margin:0;padding:0}}
  .w{{max-width:600px;margin:40px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08)}}
  .h{{background:#1a1a2e;padding:28px 40px}}.h h1{{color:#fff;font-size:20px;font-weight:700;margin:0}}
  .h p{{color:#8888aa;font-size:13px;margin:4px 0 0}}
  .b{{padding:32px 40px;color:#333;line-height:1.7;font-size:15px}}
  .b p{{margin:0 0 16px}}
  .f{{background:#f9f9f9;padding:16px 40px;border-top:1px solid #eee;font-size:12px;color:#aaa}}
</style></head><body>
<div class="w">
  <div class="h"><h1>Sportskeeda</h1><p>Application Update</p></div>
  <div class="b">
    <p>Hi {first},</p>
    <p>Thank you for taking the time to interview for the <strong>Associate Product Manager</strong> role at Sportskeeda. We genuinely appreciate the effort you put in.</p>
    <p>After careful consideration, we've decided to move forward with other candidates whose profiles more closely match our current requirements. This was not an easy decision — the competition was strong.</p>
    <p>We'd encourage you to keep building on your skills and not let this discourage you. Product management is a journey, and the curiosity and initiative you bring are real assets.</p>
    <p>We'll keep your profile on file and may reach out if a suitable opportunity arises in the future. We wish you the very best in your career.</p>
    <p>Warm regards,<br><strong>Talent Team</strong><br>Sportskeeda</p>
  </div>
  <div class="f">This is an automated message from Sportskeeda's hiring system.</div>
</div></body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = YOUR_EMAIL
    msg["To"] = candidate_email
    msg.attach(MIMEText(html, "html"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gmail.users().messages().send(userId="me", body={"raw": raw}).execute()

    # Also notify yourself
    notify_subject = f"[Interview Complete] {candidate_name} — {verdict} ({score}/10)"
    notify_body = f"Candidate: {candidate_name}\nEmail: {candidate_email}\nVerdict: {verdict}\nScore: {score}/10\n\nCheck your Google Sheet for the full report."
    notify_msg = MIMEText(notify_body)
    notify_msg["Subject"] = notify_subject
    notify_msg["From"] = YOUR_EMAIL
    notify_msg["To"] = YOUR_EMAIL
    raw2 = base64.urlsafe_b64encode(notify_msg.as_bytes()).decode()
    gmail.users().messages().send(userId="me", body={"raw": raw2}).execute()

# ─── WEBHOOK ENDPOINT ────────────────────────────────────────────────────
@app.route("/report", methods=["POST"])
def receive_report():
    try:
        data = request.get_json()
        report = data.get("report", {})

        gmail, sheets = get_services()
        ensure_report_sheet(sheets)
        write_report_to_sheet(sheets, data, report)

        send_outcome_email(
            gmail,
            data.get("candidate_name", "Candidate"),
            data.get("candidate_email", ""),
            report.get("verdict", "Rejected"),
            report.get("job_fit_score", 0)
        )

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
