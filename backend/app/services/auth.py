"""Cognito JWT verification helpers."""

from __future__ import annotations

import base64
import datetime as dt
import json
import threading
import time
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional

from ..core.config import Settings

try:  # pragma: no cover - optional dependency for production mode
    import jwt  # type: ignore
except ImportError:  # pragma: no cover - degrade when PyJWT unavailable
    jwt = None  # type: ignore


class JWTVerificationError(Exception):
    """Raised when a JWT cannot be verified."""


@dataclass(frozen=True)
class Principal:
    """Authenticated request principal extracted from JWT claims."""

    subject: str
    email: Optional[str]
    groups: frozenset[str]
    claims: Mapping[str, Any]

    @property
    def is_admin(self) -> bool:
        return "admin" in {group.lower() for group in self.groups}


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _load_json(segment: str) -> Mapping[str, Any]:
    return json.loads(_b64url_decode(segment).decode("utf-8"))


class CognitoJWKSCache:
    """Cache for JWKS documents with simple in-memory storage."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jwks: Dict[str, tuple[float, Mapping[str, Any]]] = {}
        self._ttl_seconds = 600

    def get_jwk(self, issuer: str, kid: str) -> Mapping[str, Any]:
        now = time.time()
        cache_key = f"{issuer}:{kid}"
        with self._lock:
            if cache_key in self._jwks:
                expires_at, jwk = self._jwks[cache_key]
                if now < expires_at:
                    return jwk
        jwks_uri = f"{issuer}/.well-known/jwks.json"
        with urllib.request.urlopen(jwks_uri) as response:  # pragma: no cover - network
            payload = json.loads(response.read().decode("utf-8"))
        keys: Iterable[Mapping[str, Any]] = payload.get("keys", [])
        for jwk in keys:
            if jwk.get("kid") == kid:
                with self._lock:
                    self._jwks[cache_key] = (now + self._ttl_seconds, jwk)
                return jwk
        raise JWTVerificationError("Matching JWK not found for token")


class CognitoJWTVerifier:
    """Verify Cognito-issued JWTs with optional local test mode."""

    def __init__(
        self, settings: Settings, cache: CognitoJWKSCache | None = None
    ) -> None:
        self._settings = settings
        self._cache = cache or CognitoJWKSCache()

    @property
    def _issuer(self) -> str:
        region = self._settings.region
        pool_id = self._settings.cognito_user_pool_id
        if not pool_id:
            raise JWTVerificationError("COGNITO_USER_POOL_ID is not configured")
        return f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"

    def verify(self, token: str) -> Mapping[str, Any]:
        if self._settings.cognito_test_mode:
            return self._verify_hs256(token)
        if jwt is None:
            raise JWTVerificationError(
                "PyJWT is required for Cognito verification. Install the 'PyJWT' package."
            )
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise JWTVerificationError("Token header missing 'kid'")
        jwk = self._cache.get_jwk(self._issuer, kid)
        audience = self._settings.cognito_audience or self._settings.cognito_client_id
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))  # type: ignore[attr-defined]
        try:
            payload = jwt.decode(
                token,
                key=public_key,
                algorithms=[unverified_header.get("alg", "RS256")],
                audience=audience,
                issuer=self._issuer,
                options={"verify_aud": audience is not None},
            )
        except Exception as exc:  # pragma: no cover - PyJWT error surface
            raise JWTVerificationError(str(exc)) from exc
        return payload

    def _verify_hs256(self, token: str) -> Mapping[str, Any]:
        secret = self._settings.cognito_test_shared_secret or "test-secret"
        segments = token.split(".")
        if len(segments) != 3:
            raise JWTVerificationError("Invalid JWT format")
        header = _load_json(segments[0])
        if header.get("alg") != "HS256":
            raise JWTVerificationError("Only HS256 supported in test mode")
        payload = _load_json(segments[1])
        signing_input = f"{segments[0]}.{segments[1]}".encode("utf-8")
        import hashlib
        import hmac

        signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256)
        expected = base64.urlsafe_b64encode(signature.digest()).rstrip(b"=")
        if not hmac.compare_digest(expected.decode("utf-8"), segments[2]):
            raise JWTVerificationError("Invalid signature")
        exp = payload.get("exp")
        if exp is not None:
            expires_at = dt.datetime.fromtimestamp(int(exp), tz=dt.timezone.utc)
            if expires_at < dt.datetime.now(dt.timezone.utc):
                raise JWTVerificationError("Token has expired")
        return payload


def principal_from_claims(claims: Mapping[str, Any]) -> Principal:
    subject = str(claims.get("sub"))
    email = claims.get("email")
    groups: Iterable[str] = claims.get("cognito:groups", [])
    if isinstance(groups, str):
        groups = [groups]
    return Principal(
        subject=subject, email=email, groups=frozenset(groups), claims=claims
    )
