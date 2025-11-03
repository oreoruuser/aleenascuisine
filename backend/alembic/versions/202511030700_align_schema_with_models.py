"""Align order and payment tables with current application models.

Revision ID: 202511030700
Revises: 202511020130
Create Date: 2025-11-03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision = "202511030700"
down_revision = "202511020130"
branch_labels = None
depends_on = None


_TABLES_TO_DROP = (
    "payment_events",
    "webhook_logs",
    "audit_log",
    "invoices",
    "refunds",
    "payments",
    "order_items",
    "orders",
    "razorpay_events",
)


def _drop_table_if_exists(table_name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name in inspector.get_table_names():
        op.drop_table(table_name)


def upgrade() -> None:
    # Remove legacy tables so we can recreate them with the expected schema.
    for table_name in _TABLES_TO_DROP:
        _drop_table_if_exists(table_name)

    op.create_table(
        "orders",
        sa.Column("order_id", sa.String(length=36), primary_key=True),
        sa.Column(
            "cart_id",
            sa.String(length=36),
            sa.ForeignKey("carts.cart_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "customer_id",
            sa.String(length=36),
            sa.ForeignKey("customers.customer_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "payment_status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default="INR",
        ),
        sa.Column(
            "subtotal",
            mysql.DECIMAL(precision=10, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "taxes",
            mysql.DECIMAL(precision=10, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "shipping",
            mysql.DECIMAL(precision=10, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total",
            mysql.DECIMAL(precision=10, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("provider_order_id", sa.String(length=64), nullable=True),
        sa.Column("provider_payment_id", sa.String(length=64), nullable=True),
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
        sa.Column(
            "is_test",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
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
        sa.Column(
            "reservation_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "inventory_released",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.UniqueConstraint("idempotency_key", name="uq_orders_idempotency_key"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_payment_status", "orders", ["payment_status"])
    op.create_index(
        "ix_orders_customer_created",
        "orders",
        ["customer_id", "created_at"],
    )
    op.create_index("ix_orders_cart", "orders", ["cart_id"])
    op.create_index(
        "ix_orders_reservation_expires_at",
        "orders",
        ["reservation_expires_at"],
    )

    op.create_table(
        "order_items",
        sa.Column("order_item_id", sa.String(length=36), primary_key=True),
        sa.Column(
            "order_id",
            sa.String(length=36),
            sa.ForeignKey("orders.order_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "cake_id",
            sa.String(length=36),
            sa.ForeignKey("cakes.cake_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "price_each",
            mysql.DECIMAL(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column(
            "line_total",
            mysql.DECIMAL(precision=10, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        sa.CheckConstraint("price_each >= 0", name="ck_order_items_price_non_negative"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_order_items_order", "order_items", ["order_id"])
    op.create_index("ix_order_items_cake", "order_items", ["cake_id"])

    op.create_table(
        "payments",
        sa.Column("payment_id", sa.String(length=36), primary_key=True),
        sa.Column(
            "order_id",
            sa.String(length=36),
            sa.ForeignKey("orders.order_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "amount",
            mysql.DECIMAL(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default="INR",
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="initiated",
        ),
        sa.Column("provider_payment_id", sa.String(length=64), nullable=True),
        sa.Column(
            "is_test",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
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
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_payments_order", "payments", ["order_id"])
    op.create_index(
        "ix_payments_provider_payment",
        "payments",
        ["provider_payment_id"],
    )

    op.create_table(
        "refunds",
        sa.Column("refund_id", sa.String(length=36), primary_key=True),
        sa.Column(
            "payment_id",
            sa.String(length=36),
            sa.ForeignKey("payments.payment_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "amount",
            mysql.DECIMAL(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_refunds_payment", "refunds", ["payment_id"])

    op.create_table(
        "invoices",
        sa.Column("invoice_id", sa.String(length=36), primary_key=True),
        sa.Column(
            "order_id",
            sa.String(length=36),
            sa.ForeignKey("orders.order_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("s3_bucket", sa.String(length=128), nullable=False),
        sa.Column("s3_key", sa.String(length=256), nullable=False),
        sa.Column(
            "total",
            mysql.DECIMAL(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column(
            "taxes",
            mysql.DECIMAL(precision=10, scale=2),
            nullable=False,
        ),
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

    op.create_table(
        "razorpay_events",
        sa.Column("event_id", sa.String(length=36), primary_key=True),
        sa.Column("signature", sa.String(length=256), nullable=True),
        sa.Column("headers_json", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index(
        "ix_razorpay_events_created_at",
        "razorpay_events",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_razorpay_events_created_at", table_name="razorpay_events")
    op.drop_table("razorpay_events")

    op.drop_index("ix_invoices_order", table_name="invoices")
    op.drop_table("invoices")

    op.drop_index("ix_refunds_payment", table_name="refunds")
    op.drop_table("refunds")

    op.drop_index("ix_payments_provider_payment", table_name="payments")
    op.drop_index("ix_payments_order", table_name="payments")
    op.drop_table("payments")

    op.drop_index("ix_order_items_cake", table_name="order_items")
    op.drop_index("ix_order_items_order", table_name="order_items")
    op.drop_table("order_items")

    op.drop_index("ix_orders_reservation_expires_at", table_name="orders")
    op.drop_index("ix_orders_cart", table_name="orders")
    op.drop_index("ix_orders_customer_created", table_name="orders")
    op.drop_index("ix_orders_payment_status", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_table("orders")

    # Restore the previous schema definitions from early revisions.
    op.create_table(
        "orders",
        sa.Column("order_id", sa.String(length=36), primary_key=True),
        sa.Column(
            "customer_id",
            sa.String(length=36),
            sa.ForeignKey("customers.customer_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "order_total",
            mysql.DECIMAL(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "paid",
                "cancelled",
                "shipped",
                "delivered",
                name="order_status_enum",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
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
        sa.UniqueConstraint("idempotency_key", name="uq_orders_idempotency_key"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index(
        "ix_orders_customer_created",
        "orders",
        ["customer_id", "created_at"],
    )
    op.create_index("ix_orders_status", "orders", ["status"])

    op.create_table(
        "order_items",
        sa.Column("order_item_id", sa.String(length=36), primary_key=True),
        sa.Column(
            "order_id",
            sa.String(length=36),
            sa.ForeignKey("orders.order_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "cake_id",
            sa.String(length=36),
            sa.ForeignKey("cakes.cake_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "price_each",
            mysql.DECIMAL(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        sa.CheckConstraint("price_each >= 0", name="ck_order_items_price_non_negative"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_order_items_order", "order_items", ["order_id"])
    op.create_index("ix_order_items_cake", "order_items", ["cake_id"])

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
        sa.Column(
            "is_test",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("provider_order_id", sa.String(length=100), nullable=False),
        sa.Column("provider_payment_id", sa.String(length=120), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "initiated",
                "success",
                "failed",
                "refunded",
                name="payment_status_enum",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
            server_default="initiated",
        ),
        sa.Column(
            "amount",
            mysql.DECIMAL(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default="INR",
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
    op.create_index(
        "ix_payments_provider_payment",
        "payments",
        ["provider_payment_id"],
    )

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
            "status",
            sa.Enum(
                "pending",
                "processed",
                "failed",
                name="payment_event_status_enum",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
            server_default="pending",
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
    op.create_index(
        "ix_payment_events_payment",
        "payment_events",
        ["payment_id"],
    )
    op.create_index(
        "ix_payment_events_provider",
        "payment_events",
        ["provider"],
    )

    op.create_table(
        "webhook_logs",
        sa.Column("webhook_log_id", sa.String(length=36), primary_key=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("headers", sa.JSON(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
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
    op.create_index(
        "ix_audit_log_entity",
        "audit_log",
        ["entity_type", "entity_id"],
    )

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
