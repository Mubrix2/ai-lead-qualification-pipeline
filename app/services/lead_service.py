# app/services/lead_service.py
import logging
from datetime import datetime
import requests
from app.config import (
    AIRTABLE_API_KEY,
    AIRTABLE_BASE_ID,
    AIRTABLE_TABLE_NAME,
    SLACK_WEBHOOK_URL,
)
from app.core.qualifier import qualify_lead, LeadScore

logger = logging.getLogger(__name__)


def save_to_airtable(lead_data: dict, score: LeadScore) -> str:
    """Save qualified lead to Airtable. Returns the record ID."""
    if not AIRTABLE_API_KEY:
        logger.warning("Airtable not configured — skipping save")
        return "not_configured"

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }

    # Airtable date fields require YYYY-MM-DD format only
    today = datetime.utcnow().strftime("%Y-%m-%d")

    payload = {
        "fields": {
            "Name": lead_data.get("name", ""),
            "Email": lead_data.get("email", ""),
            "Company": lead_data.get("company", ""),
            "Phone": lead_data.get("phone", ""),
            "Message": lead_data.get("message", ""),
            "Score": int(score.score),
            "Grade": score.grade,
            "Status": "New",
            "Source": lead_data.get("source", "Website"),
            "Created": today,
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        # Log exact Airtable error for debugging
        if response.status_code != 200:
            logger.error(f"Airtable error {response.status_code}: {response.text}")
            response.raise_for_status()

        record_id = response.json().get("id", "unknown")
        logger.info(f"Lead saved to Airtable: {record_id}")
        return record_id

    except requests.exceptions.HTTPError as e:
        logger.error(f"Airtable save failed: {e}")
        # Do not crash the whole pipeline if Airtable fails
        return "save_failed"


def notify_slack(lead_data: dict, score: LeadScore) -> None:
    """Send Slack notification for hot and warm leads."""
    if not SLACK_WEBHOOK_URL:
        logger.warning("Slack not configured — skipping notification")
        return

    # Only notify for hot and warm leads
    if score.grade == "COLD":
        logger.info("Cold lead — skipping Slack notification")
        return

    emoji = "🔥" if score.grade == "HOT" else "🌡️"
    colour = "#FF0000" if score.grade == "HOT" else "#FFA500"

    message = {
        "attachments": [
            {
                "color": colour,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji} {score.grade} Lead — {score.score}/100",
                        },
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Name:*\n{lead_data['name']}"},
                            {"type": "mrkdwn", "text": f"*Email:*\n{lead_data['email']}"},
                            {"type": "mrkdwn", "text": f"*Company:*\n{lead_data.get('company', 'N/A')}"},
                            {"type": "mrkdwn", "text": f"*Score:*\n{score.score}/100"},
                        ],
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Message:*\n{lead_data['message']}",
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*AI Recommendation:*\n{score.recommended_action}",
                        },
                    },
                ],
            }
        ]
    }

    response = requests.post(SLACK_WEBHOOK_URL, json=message, timeout=10)
    response.raise_for_status()
    logger.info(f"Slack notified for {score.grade} lead: {lead_data['email']}")


def process_lead(lead_data: dict) -> dict:
    """
    Full lead processing pipeline:
    qualify → save to Airtable → notify Slack if hot/warm.

    This is what the API route and n8n both call.
    """
    score = qualify_lead(
        name=lead_data["name"],
        email=lead_data["email"],
        company=lead_data.get("company", ""),
        message=lead_data["message"],
        phone=lead_data.get("phone", ""),
    )

    record_id = save_to_airtable(lead_data, score)
    notify_slack(lead_data, score)

    return {
        "name": lead_data["name"],
        "email": lead_data["email"],
        "score": score.score,
        "grade": score.grade,
        "reasoning": score.reasoning,
        "recommended_action": score.recommended_action,
        "airtable_record_id": record_id,
        "slack_notified": score.grade != "COLD",
    }