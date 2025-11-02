"""Create payments, webhook, audit, and invoice tables.

Revision ID: 202511020130
Revises: 202511020120
Create Date: 2025-11-02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision = "202511020130"
down_revision = "202511020120"
branch_labels = None
depends_on = None

PAYMENT_STATUSES = (
    "initiated",
    "success",
    "failed",
    "refunded",
)

EVENT_STATUSES = (
    "pending",
    "processed",
    "failed",
)


def _payment_status_enum() -> sa.Enum:
    return sa.Enum(
        *PAYMENT_STATUSES,
        name="payment_status_enum",
        native_enum=False,
        create_constraint=True,
    )


def _event_status_enum() -> sa.Enum:
    return sa.Enum(
        *EVENT_STATUSES,
        name="payment_event_status_enum",
        native_enum=False,
        create_constraint=True,
    )


def upgrade() -> None:
    payment_status_enum = _payment_status_enum()

    event_status_enum = _event_status_enum()

    op.create_table(
        "payments",
        sa.Column("payment_id", sa.String(length=36), primary_key=True),
        sa.Column(
            "order_id",
            sa.String(length=36),
            sa.ForeignKey("orders.order_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("is_test", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("provider_order_id", sa.String(length=100), nullable=False),
        sa.Column("provider_payment_id", sa.String(length=120), nullable=True),
        sa.Column(
            "status", payment_status_enum, nullable=False, server_default="initiated"
        ),
        sa.Column("amount", mysql.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), nullable=False, server_default="INR"
        ),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("provider_order_id", name="uq_payments_provider_order"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    op.create_index("ix_payments_order", "payments", ["order_id"])
    op.create_index("ix_payments_provider_payment", "payments", ["provider_payment_id"])

    op.create_table(
        "payment_events",
        sa.Column("payment_event_id", sa.String(length=36), primary_key=True),
        sa.Column(
            "payment_id",
            sa.String(length=36),
            sa.ForeignKey("payments.payment_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column(
            "status", event_status_enum, nullable=False, server_default="pending"
        ),
        sa.Column("headers", sa.JSON(), nullable=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    op.create_index("ix_payment_events_payment", "payment_events", ["payment_id"])
    op.create_index("ix_payment_events_provider", "payment_events", ["provider"])

    op.create_table(
        "webhook_logs",
        sa.Column("webhook_log_id", sa.String(length=36), primary_key=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("headers", sa.JSON(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "verified", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    op.create_index("ix_webhook_logs_provider", "webhook_logs", ["provider"])

    op.create_table(
        "audit_log",
        sa.Column("audit_id", sa.String(length=36), primary_key=True),
        sa.Column("actor", sa.String(length=150), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("before", sa.JSON(), nullable=True),
        sa.Column("after", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    op.create_index("ix_audit_log_entity", "audit_log", ["entity_type", "entity_id"])

    op.create_table(
        "invoices",
        sa.Column("invoice_id", sa.String(length=36), primary_key=True),
        sa.Column(
            "order_id",
            sa.String(length=36),
            sa.ForeignKey("orders.order_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    op.create_index("ix_invoices_order", "invoices", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_payments_order", table_name="payments")
    op.drop_index("ix_invoices_order", table_name="invoices")
    op.drop_table("invoices")
    op.drop_index("ix_audit_log_entity", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index("ix_webhook_logs_provider", table_name="webhook_logs")
    op.drop_table("webhook_logs")
    op.drop_index("ix_payment_events_provider", table_name="payment_events")
    op.drop_index("ix_payment_events_payment", table_name="payment_events")
    op.drop_table("payment_events")
    op.drop_index("ix_payments_provider_payment", table_name="payments")
    op.drop_table("payments")
    _payment_status_enum().drop(op.get_bind(), checkfirst=False)
    _event_status_enum().drop(op.get_bind(), checkfirst=False)
