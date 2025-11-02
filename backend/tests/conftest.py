from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.deps import razorpay_service  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.db.session import Base, configure_engine, reset_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.services.razorpay import StubRazorpayService  # noqa: E402

TEST_DB_URL = "sqlite+pysqlite:///:memory:"
ADMIN_TOKEN = "test-admin-token"


@pytest.fixture(autouse=True)
def _bootstrap_env() -> Iterator[None]:
    os.environ.setdefault("API_PREFIX", "/api/v1")
    os.environ.setdefault("DATABASE_URL", TEST_DB_URL)
    os.environ.setdefault("ADMIN_API_TOKEN", ADMIN_TOKEN)
    os.environ.setdefault("RAZORPAY_KEY_ID", "rzp_test_RaplDoujSCyeTZ")
    os.environ.setdefault("RAZORPAY_KEY_SECRET", "KKy4v6AMiv9VOAMDKbV4H12a")
    os.environ.setdefault("RAZORPAY_WEBHOOK_SECRET", "test-webhook-secret")
    os.environ.setdefault("COGNITO_TEST_MODE", "true")
    os.environ.setdefault("COGNITO_TEST_SHARED_SECRET", "unit-test-secret")
    os.environ.setdefault("COGNITO_ADMIN_GROUP", "aleena-admins")
    os.environ.setdefault("S3_BUCKET_INVOICES", "test-invoices")
    get_settings.cache_clear()
    reset_engine()
    engine = configure_engine(TEST_DB_URL)
    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=engine)
        reset_engine()
        get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _override_razorpay() -> Iterator[None]:
    stub = StubRazorpayService()
    app.dependency_overrides[razorpay_service] = lambda: stub
    try:
        yield
    finally:
        app.dependency_overrides.pop(razorpay_service, None)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_headers() -> dict[str, str]:
    token = _issue_test_token(groups=["aleena-admins"])
    return {"Authorization": f"Bearer {token}"}


def _issue_test_token(
    *, subject: str = "admin", groups: list[str] | None = None
) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "email": "admin@example.com",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    if groups:
        payload["cognito:groups"] = groups
    secret = os.environ.get("COGNITO_TEST_SHARED_SECRET", "unit-test-secret")
    header_segment = _b64url(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    payload_segment = _b64url(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signing_input = f"{header_segment}.{payload_segment}"
    signature = _sign(signing_input.encode("utf-8"), secret)
    return f"{signing_input}.{signature}"


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("utf-8")


def _sign(message: bytes, secret: str) -> str:
    import hashlib
    import hmac

    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("utf-8")
