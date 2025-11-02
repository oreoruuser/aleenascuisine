"""Create shopping cart tables.

Revision ID: 202511020110
Revises: 202511020100
Create Date: 2025-11-02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision = "202511020110"
down_revision = "202511020100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "carts",
        sa.Column("cart_id", sa.String(length=36), primary_key=True),
        sa.Column(
            "customer_id",
            sa.String(length=36),
            sa.ForeignKey("customers.customer_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("cart_token", sa.String(length=64), nullable=True),
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
        sa.UniqueConstraint("cart_token", name="uq_carts_cart_token"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    op.create_index("ix_carts_customer", "carts", ["customer_id"])

    op.create_table(
        "cart_items",
        sa.Column("cart_item_id", sa.String(length=36), primary_key=True),
        sa.Column(
            "cart_id",
            sa.String(length=36),
            sa.ForeignKey("carts.cart_id", ondelete="CASCADE"),
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
        sa.CheckConstraint("quantity > 0", name="ck_cart_items_quantity_positive"),
        sa.CheckConstraint("price_each >= 0", name="ck_cart_items_price_non_negative"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    op.create_index("ix_cart_items_cart", "cart_items", ["cart_id"])
    op.create_index("ix_cart_items_cake", "cart_items", ["cake_id"])


def downgrade() -> None:
    op.drop_index("ix_carts_customer", table_name="carts")
    op.drop_index("ix_cart_items_cake", table_name="cart_items")
    op.drop_index("ix_cart_items_cart", table_name="cart_items")
    op.drop_table("cart_items")
    op.drop_table("carts")
