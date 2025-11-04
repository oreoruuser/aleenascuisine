"""Schemas related to Cognito authentication workflows."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ConfirmSignupRequest(BaseModel):
    """Payload required to confirm a Cognito hosted UI sign up."""

    username: str = Field(..., min_length=1, strip_whitespace=True)
    code: str = Field(..., min_length=1, strip_whitespace=True)


class ConfirmSignupResponse(BaseModel):
    """Response returned after a successful confirmation."""

    message: str = Field(default="Account confirmed successfully")
