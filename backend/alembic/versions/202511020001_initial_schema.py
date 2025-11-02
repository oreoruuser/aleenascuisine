"""Initial application schema for Aleena's Cuisine.

Revision ID: 202511020001
Revises:
Create Date: 2025-11-02 00:01:00.000000
"""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision = "202511020001"
down_revision = None
branch_labels = None
depends_on = None


def _utcnow() -> datetime:
    # Helper to generate consistent timestamps for seed rows.
    return datetime.utcnow().replace(microsecond=0)


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("public_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=True),
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
            onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "cakes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("public_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", mysql.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), nullable=False, server_default="INR"
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")
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
            onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "inventory",
        sa.Column(
            "cake_id",
            sa.BigInteger(),
            sa.ForeignKey("cakes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "reorder_threshold", sa.Integer(), nullable=False, server_default="5"
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("quantity >= 0", name="ck_inventory_quantity_non_negative"),
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("public_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column(
            "customer_id",
            sa.BigInteger(),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="pending"
        ),
        sa.Column("total_amount", mysql.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), nullable=False, server_default="INR"
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
            onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("total_amount >= 0", name="ck_orders_total_amount_positive"),
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "order_items",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "order_id",
            sa.BigInteger(),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "cake_id",
            sa.BigInteger(),
            sa.ForeignKey("cakes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", mysql.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column("line_total", mysql.DECIMAL(precision=10, scale=2), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        sa.CheckConstraint("line_total >= 0", name="ck_order_items_total_positive"),
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "order_id",
            sa.BigInteger(),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("public_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column(
            "provider_reference", sa.String(length=120), nullable=False, unique=True
        ),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="created"
        ),
        sa.Column("amount", mysql.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), nullable=False, server_default="INR"
        ),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("amount >= 0", name="ck_payments_amount_positive"),
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("actor", sa.String(length=150), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        mysql_charset="utf8mb4",
    )

    op.create_index(
        "ix_orders_customer_id_created_at", "orders", ["customer_id", "created_at"]
    )
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])
    op.create_index("ix_order_items_cake_id", "order_items", ["cake_id"])
    op.create_index("ix_payments_order_status", "payments", ["order_id", "status"])

    # Seed baseline reference data so smoke tests can validate integrations quickly.
    now = _utcnow()

    customers_table = table(
        "customers",
        column("id", sa.BigInteger()),
        column("public_id", sa.String()),
        column("email", sa.String()),
        column("full_name", sa.String()),
        column("phone_number", sa.String()),
        column("created_at", sa.DateTime()),
        column("updated_at", sa.DateTime()),
    )

    cakes_table = table(
        "cakes",
        column("id", sa.BigInteger()),
        column("public_id", sa.String()),
        column("name", sa.String()),
        column("slug", sa.String()),
        column("description", sa.Text()),
        column("price", mysql.DECIMAL(10, 2)),
        column("currency", sa.String()),
        column("created_at", sa.DateTime()),
        column("updated_at", sa.DateTime()),
    )

    inventory_table = table(
        "inventory",
        column("cake_id", sa.BigInteger()),
        column("quantity", sa.Integer()),
        column("reorder_threshold", sa.Integer()),
        column("updated_at", sa.DateTime()),
    )

    orders_table = table(
        "orders",
        column("id", sa.BigInteger()),
        column("public_id", sa.String()),
        column("customer_id", sa.BigInteger()),
        column("status", sa.String()),
        column("total_amount", mysql.DECIMAL(10, 2)),
        column("currency", sa.String()),
        column("created_at", sa.DateTime()),
        column("updated_at", sa.DateTime()),
    )

    order_items_table = table(
        "order_items",
        column("id", sa.BigInteger()),
        column("order_id", sa.BigInteger()),
        column("cake_id", sa.BigInteger()),
        column("quantity", sa.Integer()),
        column("unit_price", mysql.DECIMAL(10, 2)),
        column("line_total", mysql.DECIMAL(10, 2)),
    )

    payments_table = table(
        "payments",
        column("id", sa.BigInteger()),
        column("order_id", sa.BigInteger()),
        column("public_id", sa.String()),
        column("provider", sa.String()),
        column("provider_reference", sa.String()),
        column("status", sa.String()),
        column("amount", mysql.DECIMAL(10, 2)),
        column("currency", sa.String()),
        column("created_at", sa.DateTime()),
    )

    first_customer_id = 1
    second_customer_id = 2
    first_cake_id = 1
    second_cake_id = 2
    third_cake_id = 3
    first_order_id = 1

    op.bulk_insert(
        customers_table,
        [
            {
                "id": first_customer_id,
                "public_id": str(uuid.uuid4()),
                "email": "demo.customer@aleenascuisine.test",
                "full_name": "Demo Customer",
                "phone_number": "+91-99999-11111",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": second_customer_id,
                "public_id": str(uuid.uuid4()),
                "email": "beta.tester@aleenascuisine.test",
                "full_name": "Beta Tester",
                "phone_number": "+91-99999-22222",
                "created_at": now,
                "updated_at": now,
            },
        ],
    )

    op.bulk_insert(
        cakes_table,
        [
            {
                "id": first_cake_id,
                "public_id": str(uuid.uuid4()),
                "name": "Classic Chocolate Truffle",
                "slug": "classic-chocolate-truffle",
                "description": "Dark chocolate sponge layered with ganache.",
                "price": 899.00,
                "currency": "INR",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": second_cake_id,
                "public_id": str(uuid.uuid4()),
                "name": "Strawberry Cheesecake",
                "slug": "strawberry-cheesecake",
                "description": "Baked cheesecake topped with seasonal strawberries.",
                "price": 1099.00,
                "currency": "INR",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": third_cake_id,
                "public_id": str(uuid.uuid4()),
                "name": "Biscoff Crunch",
                "slug": "biscoff-crunch",
                "description": "Speculoos-infused mousse with caramel glaze.",
                "price": 1199.00,
                "currency": "INR",
                "created_at": now,
                "updated_at": now,
            },
        ],
    )

    op.bulk_insert(
        inventory_table,
        [
            {
                "cake_id": first_cake_id,
                "quantity": 15,
                "reorder_threshold": 5,
                "updated_at": now,
            },
            {
                "cake_id": second_cake_id,
                "quantity": 10,
                "reorder_threshold": 5,
                "updated_at": now,
            },
            {
                "cake_id": third_cake_id,
                "quantity": 8,
                "reorder_threshold": 4,
                "updated_at": now,
            },
        ],
    )

    op.bulk_insert(
        orders_table,
        [
            {
                "id": first_order_id,
                "public_id": str(uuid.uuid4()),
                "customer_id": first_customer_id,
                "status": "processing",
                "total_amount": 1998.00,
                "currency": "INR",
                "created_at": now,
                "updated_at": now,
            }
        ],
    )

    op.bulk_insert(
        order_items_table,
        [
            {
                "id": 1,
                "order_id": first_order_id,
                "cake_id": first_cake_id,
                "quantity": 1,
                "unit_price": 899.00,
                "line_total": 899.00,
            },
            {
                "id": 2,
                "order_id": first_order_id,
                "cake_id": second_cake_id,
                "quantity": 1,
                "unit_price": 1099.00,
                "line_total": 1099.00,
            },
        ],
    )

    op.bulk_insert(
        payments_table,
        [
            {
                "id": 1,
                "order_id": first_order_id,
                "public_id": str(uuid.uuid4()),
                "provider": "razorpay",
                "provider_reference": "rzp_test_demo_payment",
                "status": "captured",
                "amount": 1998.00,
                "currency": "INR",
                "created_at": now,
            }
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_payments_order_status", table_name="payments")
    op.drop_index("ix_order_items_cake_id", table_name="order_items")
    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_customer_id_created_at", table_name="orders")

    op.drop_table("audit_log")
    op.drop_table("payments")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("inventory")
    op.drop_table("cakes")
    op.drop_table("customers")
