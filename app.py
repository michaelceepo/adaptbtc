import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
from learning_portal.portal_routes import portal

load_dotenv()

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")

# Register Learning Portal blueprint
app.register_blueprint(portal)


# ------------------------------
# MAIN SITE ROUTES
# ------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/tools")
def tools():
    return render_template("tools.html")


@app.route("/consulting")
def consulting():
    return render_template("consulting.html")


@app.route("/donate")
def donate():
    return render_template("donate.html")


@app.route("/donation")
def donation():
    return render_template("donation.html")


@app.route("/learning")
def learning():
    return render_template("learning.html")


# ------------------------------
# TOOL ROUTES
# ------------------------------

@app.route("/tools/live-feed")
def live_feed():
    return render_template("tools/live-feed.html")


@app.route("/tools/dca")
def dca():
    return render_template("tools/dca.html")


# Static assets for DCA Tool
@app.route("/tools/dca/assets/<path:filename>")
def dca_asset(filename):
    return send_from_directory(os.path.join("tools", "dca"), filename)


# ------------------------------
# ERROR HANDLERS
# ------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("errors/500.html"), 500


# ------------------------------
# API ROUTES
# ------------------------------


def _send_consulting_email(payload: dict) -> None:
    """Send consulting request details to support@adaptbtc.com via SMTP."""

    support_email = "support@adaptbtc.com"
    from_email = os.getenv("CONSULTING_FROM_EMAIL", support_email)
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() != "false"

    if not smtp_host:
        raise RuntimeError(
            "Email delivery is not configured on the server. "
            "Please contact support@adaptbtc.com directly."
        )

    msg = EmailMessage()
    msg["Subject"] = "New AdaptBTC consulting request"
    msg["From"] = from_email
    msg["To"] = support_email
    if payload.get("email"):
        msg["Reply-To"] = payload["email"]

    details = payload.get("details") or "(no additional details provided)"

    msg.set_content(
        "\n".join(
            [
                "A new consulting request was submitted via adaptbtc.com.",
                "",
                f"Name: {payload.get('name', 'N/A')}",
                f"Email: {payload.get('email', 'N/A')}",
                f"Engagement: {payload.get('engagement', 'N/A')}",
                f"Team size: {payload.get('team_size', 'N/A')}",
                "",
                "Notes:",
                details,
            ]
        )
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
        if use_tls:
            smtp.starttls()
        if smtp_user and smtp_password:
            smtp.login(smtp_user, smtp_password)
        smtp.send_message(msg)


@app.post("/api/consulting/request")
def submit_consulting_request():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    engagement = (data.get("engagement") or "").strip()
    team_size = (data.get("team_size") or "").strip()
    details = (data.get("details") or "").strip()

    if not name or not email or not engagement or not team_size:
        return jsonify({"error": "Please complete all required fields."}), 400

    if "@" not in email:
        return jsonify({"error": "Enter a valid email address."}), 400

    try:
        _send_consulting_email(
            {
                "name": name,
                "email": email,
                "engagement": engagement,
                "team_size": team_size,
                "details": details,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return (
            jsonify({"error": f"Unable to send request: {exc}"}),
            500,
        )

    return jsonify({"ok": True})


# ------------------------------
# MAIN ENTRY
# ------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
