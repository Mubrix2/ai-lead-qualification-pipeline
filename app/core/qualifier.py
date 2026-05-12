# app/core/qualifier.py
import logging
from pydantic import BaseModel, Field
import instructor
from groq import Groq
from app.config import GROQ_API_KEY, LLM_MODEL
from app.core.prompts import QUALIFICATION_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_client = None


def get_client():
    global _client
    if _client is None:
        raw = Groq(api_key=GROQ_API_KEY)
        _client = instructor.from_groq(raw, mode=instructor.Mode.JSON)
        logger.info("Qualifier client initialised")
    return _client


class LeadScore(BaseModel):
    """Structured lead qualification result."""
    score: int = Field(
        ge=0, le=100,
        description="Lead quality score from 0 to 100"
    )
    grade: str = Field(
        description="HOT, WARM, or COLD based on score"
    )
    reasoning: str = Field(
        description="Two sentence explanation of the score"
    )
    recommended_action: str = Field(
        description="Specific next action for the sales team"
    )


def qualify_lead(
    name: str,
    email: str,
    company: str,
    message: str,
    phone: str = "",
) -> LeadScore:
    """
    Score and grade an incoming lead using the LLM.

    Returns a LeadScore with score, grade, reasoning,
    and recommended action for the sales team.
    """
    client = get_client()

    lead_context = f"""
Lead Information:
- Name: {name}
- Email: {email}
- Company: {company}
- Phone: {phone or 'Not provided'}
- Message: {message}
"""

    logger.info(f"Qualifying lead from: {email}")

    result: LeadScore = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": QUALIFICATION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Qualify this lead:\n{lead_context}"},
        ],
        response_model=LeadScore,
        temperature=0.1,
        max_tokens=300,
    )

    logger.info(f"Lead scored: {result.score}/100 — {result.grade}")
    return result