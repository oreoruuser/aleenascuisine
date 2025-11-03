"""Runtime configuration helpers for the Aleena's Cuisine API."""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import ClassVar, Optional
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_prefix: str = Field("/api/v1", alias="API_PREFIX")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    region: str = Field("ap-south-1", alias="REGION")
    aleena_env: str = Field("dev", alias="ALEENA_ENV")

    db_cluster_arn: Optional[str] = Field(None, alias="DB_RESOURCE_ARN")
    db_secret_arn: Optional[str] = Field(None, alias="DB_SECRET_ARN")
    database_url: Optional[str] = Field(None, alias="DATABASE_URL")
    db_host: Optional[str] = Field(None, alias="DB_HOST")
    db_port: int = Field(3306, alias="DB_PORT")
    db_name: str = Field("aleenascuisine", alias="DB_NAME")
    cognito_user_pool_id: Optional[str] = Field(None, alias="COGNITO_USER_POOL_ID")
    cognito_client_id: Optional[str] = Field(None, alias="COGNITO_CLIENT_ID")
    cognito_client_secret_arn: Optional[str] = Field(
        None, alias="COGNITO_CLIENT_SECRET_ARN"
    )

    razorpay_secret_arn: Optional[str] = Field(None, alias="RAZORPAY_SECRET_ARN")
    whatsapp_secret_arn: Optional[str] = Field(None, alias="WHATSAPP_SECRET_ARN")
    razorpay_key_id: Optional[str] = Field(None, alias="RAZORPAY_KEY_ID")
    razorpay_key_secret: Optional[str] = Field(None, alias="RAZORPAY_KEY_SECRET")
    razorpay_webhook_secret: Optional[str] = Field(
        None, alias="RAZORPAY_WEBHOOK_SECRET"
    )

    s3_bucket_images: Optional[str] = Field(None, alias="S3_BUCKET_IMAGES")
    s3_bucket_invoices: Optional[str] = Field(None, alias="S3_BUCKET_INVOICES")

    tax_rate_percent: float = Field(0.0, alias="TAX_RATE_PERCENT")
    shipping_flat_fee: float = Field(0.0, alias="SHIPPING_FLAT_FEE")
    shipping_free_threshold: float = Field(0.0, alias="SHIPPING_FREE_THRESHOLD")
    price_match_tolerance: float = Field(0.0, alias="PRICE_MATCH_TOLERANCE")
    order_reservation_ttl_minutes: int = Field(
        15, alias="ORDER_RESERVATION_TTL_MINUTES"
    )
    post_payment_queue_url: Optional[str] = Field(None, alias="POST_PAYMENT_QUEUE_URL")
    admin_notifications_topic_arn: Optional[str] = Field(
        None, alias="ADMIN_NOTIFICATIONS_TOPIC_ARN"
    )

    is_test_mode: bool = Field(False, alias="RAZORPAY_TEST_MODE")
    admin_api_token: Optional[str] = Field(None, alias="ADMIN_API_TOKEN")
    cognito_admin_group: str = Field("aleena-admins", alias="COGNITO_ADMIN_GROUP")
    cognito_audience: Optional[str] = Field(None, alias="COGNITO_AUDIENCE")
    cognito_test_mode: bool = Field(False, alias="COGNITO_TEST_MODE")
    cognito_test_shared_secret: Optional[str] = Field(
        None, alias="COGNITO_TEST_SHARED_SECRET"
    )
    whatsapp_phone_number_id: Optional[str] = Field(
        None, alias="WHATSAPP_PHONE_NUMBER_ID"
    )
    whatsapp_default_recipient: Optional[str] = Field(
        None, alias="WHATSAPP_DEFAULT_RECIPIENT"
    )
    whatsapp_api_version: str = Field("v18.0", alias="WHATSAPP_API_VERSION")

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        case_sensitive=True,
        env_file=os.environ.get("ALEENA_ENV_FILE"),
        env_file_encoding="utf-8",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""
    settings = Settings()  # type: ignore[call-arg]
    if not settings.database_url:
        derived_url = _build_database_url(settings)
        if derived_url:
            # Persist the derived URL so downstream helpers reuse the same value.
            settings.database_url = derived_url
            os.environ.setdefault("DATABASE_URL", derived_url)
    _hydrate_razorpay_credentials(settings)
    return settings


logger = logging.getLogger(__name__)


def _build_database_url(settings: Settings) -> Optional[str]:
    """Derive a SQLAlchemy URL from Secrets Manager metadata when not provided."""

    if not settings.db_secret_arn or not settings.db_host:
        return None

    try:  # Deferred import keeps local test environments lightweight.
        import boto3  # type: ignore
    except ImportError as exc:  # pragma: no cover - boto3 always available in Lambda
        raise RuntimeError("boto3 is required to resolve database credentials") from exc

    client = boto3.client("secretsmanager", region_name=settings.region)
    try:
        response = client.get_secret_value(SecretId=settings.db_secret_arn)
    except Exception as exc:  # pragma: no cover - network dependent
        logger.error(
            "Failed to fetch database credentials from Secrets Manager",
            extra={"secret_arn": settings.db_secret_arn},
            exc_info=exc,
        )
        raise RuntimeError("Unable to resolve database credentials") from exc

    secret_string = response.get("SecretString")
    if not secret_string:
        raise RuntimeError("Database secret does not contain a SecretString value")

    try:
        payload = json.loads(secret_string)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Database secret string is not valid JSON") from exc

    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise RuntimeError("Database secret missing username or password")

    port = payload.get("port") or settings.db_port
    database = payload.get("dbname") or settings.db_name
    user_enc = quote_plus(str(username))
    pass_enc = quote_plus(str(password))
    host = settings.db_host

    return f"mysql+pymysql://{user_enc}:{pass_enc}@{host}:{port}/{database}"


def _hydrate_razorpay_credentials(settings: Settings) -> None:
    """Populate Razorpay credentials from Secrets Manager when necessary."""

    if settings.razorpay_key_id and settings.razorpay_key_secret:
        return
    secret_arn = settings.razorpay_secret_arn
    if not secret_arn:
        return

    try:  # pragma: no cover - boto3 available in Lambda
        import boto3  # type: ignore
    except ImportError:  # pragma: no cover - local dev without boto3
        logger.warning(
            "boto3 unavailable; unable to load Razorpay credentials from Secrets Manager"
        )
        return

    client = boto3.client("secretsmanager", region_name=settings.region)
    try:
        response = client.get_secret_value(SecretId=secret_arn)
    except Exception as exc:  # pragma: no cover - AWS network failures
        logger.error(
            "Failed to fetch Razorpay credentials from Secrets Manager",
            extra={"secret_arn": secret_arn},
            exc_info=exc,
        )
        return

    secret_string = response.get("SecretString")
    if not secret_string:
        logger.warning(
            "Razorpay secret does not contain a SecretString value",
            extra={"secret_arn": secret_arn},
        )
        return

    try:
        payload = json.loads(secret_string)
    except json.JSONDecodeError:
        # Support plain string secrets that might only contain the key
        payload = {}
        if not settings.razorpay_key_id:
            payload["key_id"] = secret_string

    key_id = payload.get("key_id")
    key_secret = payload.get("key_secret")
    webhook_secret = payload.get("webhook_secret")

    if key_id and not settings.razorpay_key_id:
        settings.razorpay_key_id = key_id
        os.environ.setdefault("RAZORPAY_KEY_ID", key_id)
    if key_secret and not settings.razorpay_key_secret:
        settings.razorpay_key_secret = key_secret
        os.environ.setdefault("RAZORPAY_KEY_SECRET", key_secret)
    if webhook_secret and not settings.razorpay_webhook_secret:
        settings.razorpay_webhook_secret = webhook_secret
        os.environ.setdefault("RAZORPAY_WEBHOOK_SECRET", webhook_secret)
