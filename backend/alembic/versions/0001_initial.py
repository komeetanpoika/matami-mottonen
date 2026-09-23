"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-23
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("title_fi", sa.String(200)),
        sa.Column("title_en", sa.String(200)),
        sa.Column("description_fi", sa.Text),
        sa.Column("description_en", sa.Text),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("location", sa.String(300)),
        sa.Column("price_cents", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("capacity", sa.Integer, nullable=False),
        sa.Column("is_published", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("price_cents >= 0", name="ck_events_price_nonneg"),
        sa.CheckConstraint("capacity >= 1", name="ck_events_capacity_pos"),
        sa.CheckConstraint("title_fi IS NOT NULL OR title_en IS NOT NULL", name="ck_events_some_title"),
    )
    op.create_index("ix_events_starts_at", "events", ["starts_at"])
    op.create_table(
        "registrations",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("events.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("lang", sa.String(8), nullable=False, server_default="en"),
        sa.Column("stripe_session_id", sa.String(255), unique=True),
        sa.Column("stripe_payment_intent_id", sa.String(255)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("quantity BETWEEN 1 AND 10", name="ck_registrations_quantity"),
        sa.CheckConstraint(
            "status IN ('pending','confirmed','cancelled','expired')", name="ck_registrations_status"
        ),
    )
    op.create_index("ix_registrations_event_id", "registrations", ["event_id"])
    op.create_index("ix_registrations_status", "registrations", ["status"])
    op.create_index(
        "ix_registrations_stripe_payment_intent_id", "registrations", ["stripe_payment_intent_id"]
    )


def downgrade() -> None:
    op.drop_table("registrations")
    op.drop_table("events")
    op.drop_table("admin_users")
