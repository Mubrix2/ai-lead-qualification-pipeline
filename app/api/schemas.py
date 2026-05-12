# app/api/schemas.py
from pydantic import BaseModel, EmailStr, Field


class LeadRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(description="Lead email address")
    company: str = Field(default="", max_length=100)
    phone: str = Field(default="", max_length=20)
    message: str = Field(min_length=10, max_length=2000)
    source: str = Field(default="Website")


class LeadResponse(BaseModel):
    name: str
    email: str
    score: int
    grade: str
    reasoning: str
    recommended_action: str
    airtable_record_id: str
    slack_notified: bool


class HealthResponse(BaseModel):
    status: str
    env: str