# app/api/routes/leads.py
import logging
from fastapi import APIRouter, HTTPException, Header, status
from app.api.schemas import LeadRequest, LeadResponse
from app.services.lead_service import process_lead
from app.config import N8N_WEBHOOK_SECRET

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/leads", tags=["Leads"])


@router.post(
    "/qualify",
    response_model=LeadResponse,
    summary="Qualify an incoming lead using AI",
)
async def qualify_lead_endpoint(
    request: LeadRequest,
    x_webhook_secret: str = Header(default=""),
):
    """
    Receive a lead, score it with AI, save to Airtable,
    and notify Slack if hot or warm.

    Called by n8n after receiving a form submission webhook.
    Protected by webhook secret header.
    """
    # Validate webhook secret when configured
    if N8N_WEBHOOK_SECRET and x_webhook_secret != N8N_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret",
        )

    try:
        result = process_lead(lead_data=request.model_dump())
        return LeadResponse(**result)
    except Exception as e:
        logger.error(f"Lead processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lead processing failed. Please try again.",
        )