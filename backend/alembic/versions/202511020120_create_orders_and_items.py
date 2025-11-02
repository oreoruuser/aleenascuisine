"""Create orders and order_items tables.

Revision ID: 202511020120
Revises: 202511020110
Create Date: 2025-11-02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision = "202511020120"
down_revision = "202511020110"
branch_labels = None
depends_on = None

ORDER_STATUSES = (
    "pending",
    "paid",
    "cancelled",
    "shipped",
    "delivered",
)


def _order_status_enum() -> sa.Enum:
    return sa.Enum(
        *ORDER_STATUSES,
        name="order_status_enum",
        native_enum=False,
        create_constraint=True,
    )


def upgrade() -> None:
    status_enum = _order_status_enum()

    op.create_table(
        "orders",
        sa.Column("order_id", sa.String(length=36), primary_key=True),
        sa.Column(
            "customer_id",
            sa.String(length=36),
            sa.ForeignKey("customers.customer_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("order_total", mysql.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column("status", status_enum, nullable=False, server_default="pending"),
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
        sa.CheckConstraint("order_total >= 0", name="ck_orders_total_non_negative"),
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
        sa.Column("price_each", mysql.DECIMAL(precision=10, scale=2), nullable=False),
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


def downgrade() -> None:
    op.drop_index("ix_order_items_cake", table_name="order_items")
    op.drop_index("ix_order_items_order", table_name="order_items")
    op.drop_table("order_items")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_customer_created", table_name="orders")
    op.drop_table("orders")
    _order_status_enum().drop(op.get_bind(), checkfirst=False)
