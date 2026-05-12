# tests/test_qualifier.py
import pytest
from unittest.mock import patch, MagicMock
from app.core.qualifier import LeadScore
from app.services.lead_service import process_lead


@patch("app.services.lead_service.qualify_lead")
@patch("app.services.lead_service.save_to_airtable")
@patch("app.services.lead_service.notify_slack")
def test_process_lead_hot(mock_slack, mock_airtable, mock_qualify):
    mock_qualify.return_value = LeadScore(
        score=85,
        grade="HOT",
        reasoning="High urgency and budget signals present.",
        recommended_action="Call within 1 hour.",
    )
    mock_airtable.return_value = "rec123"

    result = process_lead({
        "name": "Emeka",
        "email": "emeka@test.com",
        "company": "TechCorp",
        "message": "Urgent: need chatbot this week, budget approved",
        "phone": "",
    })

    assert result["grade"] == "HOT"
    assert result["score"] == 85
    assert result["slack_notified"] is True
    mock_slack.assert_called_once()


@patch("app.services.lead_service.qualify_lead")
@patch("app.services.lead_service.save_to_airtable")
@patch("app.services.lead_service.notify_slack")
def test_process_lead_cold_no_slack(mock_slack, mock_airtable, mock_qualify):
    mock_qualify.return_value = LeadScore(
        score=30,
        grade="COLD",
        reasoning="Vague message with no urgency.",
        recommended_action="Add to nurture sequence.",
    )
    mock_airtable.return_value = "rec456"

    result = process_lead({
        "name": "Test",
        "email": "test@test.com",
        "company": "",
        "message": "I might be interested sometime maybe",
        "phone": "",
    })

    assert result["grade"] == "COLD"
    assert result["slack_notified"] is False
    mock_slack.assert_called_once()