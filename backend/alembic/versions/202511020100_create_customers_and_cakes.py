"""Create customers and cakes base tables.

Revision ID: 202511020100
Revises: None
Create Date: 2025-11-02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "202511020100"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("customer_id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("whatsapp_id", sa.String(length=64), nullable=True),
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
        sa.UniqueConstraint("email", name="uq_customers_email"),
        sa.UniqueConstraint("phone", name="uq_customers_phone"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    op.create_index(
        "ix_customers_created_at",
        "customers",
        ["created_at"],
    )

    op.create_table(
        "cakes",
        sa.Column("cake_id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", mysql.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), nullable=False, server_default="INR"
        ),
        sa.Column("image_url", sa.String(length=512), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column(
            "stock_quantity",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "is_available",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
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
        sa.CheckConstraint("price >= 0", name="ck_cakes_price_non_negative"),
        sa.CheckConstraint("stock_quantity >= 0", name="ck_cakes_stock_non_negative"),
        sa.UniqueConstraint("slug", name="uq_cakes_slug"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    op.create_index(
        "ix_cakes_category",
        "cakes",
        ["category"],
    )


def downgrade() -> None:
    op.drop_index("ix_cakes_category", table_name="cakes")
    op.drop_table("cakes")
    op.drop_index("ix_customers_created_at", table_name="customers")
    op.drop_table("customers")
