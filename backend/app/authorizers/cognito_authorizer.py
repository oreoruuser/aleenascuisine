"""Lambda request authorizer that verifies Cognito JWTs."""

from __future__ import annotations

import logging
from typing import Any, Dict, Mapping

try:
    from core.config import get_settings
    from services.auth import (
        CognitoJWTVerifier,
        JWTVerificationError,
        principal_from_claims,
    )
except ImportError:  # pragma: no cover - fallback for local package layout
    from ..core.config import get_settings
    from ..services.auth import (
        CognitoJWTVerifier,
        JWTVerificationError,
        principal_from_claims,
    )

logger = logging.getLogger(__name__)


def _extract_bearer(headers: Mapping[str, Any] | None) -> str | None:
    if not headers:
        return None
    header = headers.get("Authorization") or headers.get("authorization")
    if not header:
        return None
    if header.startswith("Bearer "):
        return header.split(" ", 1)[1].strip()
    return header.strip()


def _allow(principal_id: str, resource: str, context: Dict[str, str]) -> Dict[str, Any]:
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": resource,
                }
            ],
        },
        "context": context,
    }


def _deny(principal_id: str, resource: str) -> Dict[str, Any]:
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": resource,
                }
            ],
        },
    }


def handle(event: Dict[str, Any], _context: Any | None = None) -> Dict[str, Any]:
    method_arn = event.get("methodArn", "*")
    headers = event.get("headers") or {}
    token = _extract_bearer(headers)
    settings = get_settings()

    if not token:
        logger.info(
            "Authorizer allowing anonymous request", extra={"resource": method_arn}
        )
        return _allow(
            principal_id="anonymous",
            resource=method_arn,
            context={"is_authenticated": "false"},
        )

    verifier = CognitoJWTVerifier(settings)
    try:
        claims = verifier.verify(token)
    except JWTVerificationError as exc:
        logger.warning("JWT verification failed", extra={"reason": str(exc)})
        return _deny("unauthorized", method_arn)

    principal = principal_from_claims(claims)
    context = {
        "is_authenticated": "true",
        "subject": principal.subject,
        "email": principal.email or "",
        "groups": ",".join(sorted(principal.groups)) or "",
    }
    logger.info(
        "Authorizer validated request",
        extra={"principal": principal.subject, "resource": method_arn},
    )
    return _allow(principal.subject, method_arn, context)
