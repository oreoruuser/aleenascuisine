"""Runtime configuration helpers for the Aleena's Cuisine API."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_prefix: str = Field("/api/v1", alias="API_PREFIX")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    region: str = Field("ap-south-1", alias="REGION")
    aleena_env: str = Field("dev", alias="ALEENA_ENV")

    db_cluster_arn: Optional[str] = Field(None, alias="DB_RESOURCE_ARN")
    db_secret_arn: Optional[str] = Field(None, alias="DB_SECRET_ARN")
    database_url: Optional[str] = Field(None, alias="DATABASE_URL")
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

    is_test_mode: bool = Field(False, alias="RAZORPAY_TEST_MODE")
    admin_api_token: Optional[str] = Field(None, alias="ADMIN_API_TOKEN")
    cognito_admin_group: str = Field("aleena-admins", alias="COGNITO_ADMIN_GROUP")
    cognito_audience: Optional[str] = Field(None, alias="COGNITO_AUDIENCE")
    cognito_test_mode: bool = Field(False, alias="COGNITO_TEST_MODE")
    cognito_test_shared_secret: Optional[str] = Field(
        None, alias="COGNITO_TEST_SHARED_SECRET"
    )

    model_config = ConfigDict(
        case_sensitive=True,
        env_file=os.environ.get("ALEENA_ENV_FILE"),
        env_file_encoding="utf-8",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""

    return Settings()
