"""Initial schema with 10 tables, indexes, and v_transactions view

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-21 21:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. users
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=10), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true" if is_postgres else "1"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()" if is_postgres else "CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("role IN ('admin','staff','requester')", name="check_user_role"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("username"),
    )

    # 2. staff
    op.create_table(
        "staff",
        sa.Column("staff_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("staff_id"),
        sa.UniqueConstraint("user_id"),
    )

    # 3. requesters
    op.create_table(
        "requesters",
        sa.Column("requester_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.CheckConstraint("type IN ('hospital','patient')", name="check_requester_type"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("requester_id"),
        sa.UniqueConstraint("user_id"),
    )

    # 4. donors
    op.create_table(
        "donors",
        sa.Column("donor_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("dob", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(length=10), nullable=False),
        sa.Column("blood_group", sa.String(length=3), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("weight", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("last_donation_date", sa.Date(), nullable=True),
        sa.CheckConstraint("gender IN ('male','female','other')", name="check_donor_gender"),
        sa.CheckConstraint("blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')", name="check_donor_blood_group"),
        sa.CheckConstraint("weight > 0", name="check_donor_weight_positive"),
        sa.PrimaryKeyConstraint("donor_id"),
    )

    # 5. blood_units
    op.create_table(
        "blood_units",
        sa.Column("unit_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("donor_id", sa.Integer(), nullable=False),
        sa.Column("blood_group", sa.String(length=3), nullable=False),
        sa.Column("collection_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=10), server_default="available", nullable=False),
        sa.CheckConstraint("blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')", name="check_unit_blood_group"),
        sa.CheckConstraint("status IN ('available','issued','expired')", name="check_unit_status"),
        sa.CheckConstraint("expiry_date > collection_date", name="check_unit_expiry_after_collection"),
        sa.ForeignKeyConstraint(["donor_id"], ["donors.donor_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("unit_id"),
    )

    # 6. blood_requests
    op.create_table(
        "blood_requests",
        sa.Column("request_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("blood_group", sa.String(length=3), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("urgency", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=10), server_default="pending", nullable=False),
        sa.Column("request_date", sa.Date(), nullable=False),
        sa.CheckConstraint("blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')", name="check_request_blood_group"),
        sa.CheckConstraint("quantity >= 1", name="check_request_quantity_min"),
        sa.CheckConstraint("urgency IN ('emergency','routine')", name="check_request_urgency"),
        sa.CheckConstraint("status IN ('pending','approved','issued','rejected')", name="check_request_status"),
        sa.ForeignKeyConstraint(["requester_id"], ["requesters.requester_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("request_id"),
    )

    # 7. issue_records
    op.create_table(
        "issue_records",
        sa.Column("issue_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("issued_by", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["issued_by"], ["staff.staff_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["request_id"], ["blood_requests.request_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["unit_id"], ["blood_units.unit_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("issue_id"),
        sa.UniqueConstraint("unit_id"),
    )

    # 8. donation_camps
    op.create_table(
        "donation_camps",
        sa.Column("camp_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("camp_date", sa.Date(), nullable=False),
        sa.Column("target_units", sa.Integer(), nullable=False),
        sa.Column("units_collected", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint("target_units > 0", name="check_camp_target_units_positive"),
        sa.CheckConstraint("units_collected >= 0", name="check_camp_units_collected_non_negative"),
        sa.PrimaryKeyConstraint("camp_id"),
    )

    # 9. activity_logs
    details_col = (
        postgresql.JSONB(astext_type=sa.Text())
        if is_postgres
        else sa.JSON()
    )
    op.create_table(
        "activity_logs",
        sa.Column("log_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("entity_type", sa.String(length=30), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("details", details_col, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()" if is_postgres else "CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("log_id"),
    )

    # 10. shortage_predictions
    uuid_col = (
        postgresql.UUID(as_uuid=True)
        if is_postgres
        else sa.Uuid()
    )
    op.create_table(
        "shortage_predictions",
        sa.Column("prediction_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", uuid_col, nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("blood_group", sa.String(length=3), nullable=False),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("predicted_stock", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("safe_minimum", sa.Integer(), nullable=False),
        sa.Column("is_below_minimum", sa.Boolean(), nullable=False),
        sa.Column("model_name", sa.String(length=30), nullable=False),
        sa.CheckConstraint("blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')", name="check_pred_blood_group"),
        sa.CheckConstraint("predicted_stock >= 0", name="check_pred_stock_non_negative"),
        sa.PrimaryKeyConstraint("prediction_id"),
        sa.UniqueConstraint("run_id", "blood_group", "forecast_date", name="uq_run_group_date"),
    )

    # Section 7.3 Indexes
    op.create_index("idx_blood_units_blood_group", "blood_units", ["blood_group"])
    op.create_index("idx_blood_units_expiry_date", "blood_units", ["expiry_date"])
    op.create_index("idx_blood_units_match", "blood_units", ["status", "blood_group", "expiry_date"])
    op.create_index("idx_blood_units_donor_id", "blood_units", ["donor_id"])

    op.create_index("idx_blood_requests_requester_id", "blood_requests", ["requester_id"])
    op.create_index("idx_blood_requests_status", "blood_requests", ["status", "urgency", "request_date"])

    op.create_index("idx_issue_records_request_id", "issue_records", ["request_id"])

    op.create_index("idx_donors_blood_group", "donors", ["blood_group"])
    op.create_index("idx_donors_last_donation_date", "donors", ["last_donation_date"])

    op.create_index("idx_activity_logs_created_at", "activity_logs", ["created_at"])
    op.create_index("idx_activity_logs_user_id", "activity_logs", ["user_id"])

    op.create_index("idx_predictions_run_id", "shortage_predictions", ["run_id"])
    op.create_index("idx_predictions_generated_at", "shortage_predictions", ["generated_at"])

    # Section 7.4 Transaction View (v_transactions)
    if is_postgres:
        op.execute("""
        CREATE VIEW v_transactions AS
        SELECT 'donation'::text AS transaction_type,
               u.unit_id, u.blood_group, u.collection_date AS transaction_date,
               u.donor_id, NULL::integer AS request_id, NULL::integer AS staff_id
        FROM blood_units u
        UNION ALL
        SELECT 'issue'::text, i.unit_id, u.blood_group, i.issue_date,
               u.donor_id, i.request_id, i.issued_by
        FROM issue_records i
        JOIN blood_units u ON u.unit_id = i.unit_id
        UNION ALL
        SELECT 'wastage'::text, u.unit_id, u.blood_group, u.expiry_date,
               u.donor_id, NULL::integer, NULL::integer
        FROM blood_units u
        WHERE u.status = 'expired';
        """)
    else:
        op.execute("""
        CREATE VIEW v_transactions AS
        SELECT 'donation' AS transaction_type,
               u.unit_id, u.blood_group, u.collection_date AS transaction_date,
               u.donor_id, NULL AS request_id, NULL AS staff_id
        FROM blood_units u
        UNION ALL
        SELECT 'issue', i.unit_id, u.blood_group, i.issue_date,
               u.donor_id, i.request_id, i.issued_by
        FROM issue_records i
        JOIN blood_units u ON u.unit_id = i.unit_id
        UNION ALL
        SELECT 'wastage', u.unit_id, u.blood_group, u.expiry_date,
               u.donor_id, NULL, NULL
        FROM blood_units u
        WHERE u.status = 'expired';
        """)


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Drop view first
    if is_postgres:
        op.execute("DROP VIEW IF EXISTS v_transactions CASCADE;")
    else:
        op.execute("DROP VIEW IF EXISTS v_transactions;")

    # Drop indexes
    op.drop_index("idx_predictions_generated_at", table_name="shortage_predictions")
    op.drop_index("idx_predictions_run_id", table_name="shortage_predictions")
    op.drop_index("idx_activity_logs_user_id", table_name="activity_logs")
    op.drop_index("idx_activity_logs_created_at", table_name="activity_logs")
    op.drop_index("idx_donors_last_donation_date", table_name="donors")
    op.drop_index("idx_donors_blood_group", table_name="donors")
    op.drop_index("idx_issue_records_request_id", table_name="issue_records")
    op.drop_index("idx_blood_requests_status", table_name="blood_requests")
    op.drop_index("idx_blood_requests_requester_id", table_name="blood_requests")
    op.drop_index("idx_blood_units_donor_id", table_name="blood_units")
    op.drop_index("idx_blood_units_match", table_name="blood_units")
    op.drop_index("idx_blood_units_expiry_date", table_name="blood_units")
    op.drop_index("idx_blood_units_blood_group", table_name="blood_units")

    # Drop tables in reverse order
    op.drop_table("shortage_predictions")
    op.drop_table("activity_logs")
    op.drop_table("donation_camps")
    op.drop_table("issue_records")
    op.drop_table("blood_requests")
    op.drop_table("blood_units")
    op.drop_table("donors")
    op.drop_table("requesters")
    op.drop_table("staff")
    op.drop_table("users")
