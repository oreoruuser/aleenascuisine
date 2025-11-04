from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def handle(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    """Ensure Cognito captures email during hosted UI sign-up and requires verification."""
    user_attributes = event.setdefault("request", {}).setdefault("userAttributes", {})
    response = event.setdefault("response", {})

    username = event.get("userName", "")
    email = user_attributes.get("email")

    if not email and "@" in username:
        user_attributes["email"] = username
        user_attributes.setdefault("email_verified", "false")
        logger.info(
            "PreSignUp: populated email attribute from username",
            extra={"username": username},
        )
    elif not email:
        logger.warning(
            "PreSignUp: username does not contain '@'; email attribute remains unset",
            extra={"username": username},
        )

    # Ensure Cognito still waits for the user to confirm via the emailed code
    response.setdefault("autoConfirmUser", False)
    response.setdefault("autoVerifyEmail", False)

    return event
