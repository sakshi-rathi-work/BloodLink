import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid
from app.db.base import Base


class ShortagePrediction(Base):
    __tablename__ = "shortage_predictions"

    prediction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True).with_variant(Uuid(), "sqlite"), nullable=False
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    blood_group: Mapped[str] = mapped_column(String(3), nullable=False)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_stock: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    safe_minimum: Mapped[int] = mapped_column(Integer, nullable=False)
    is_below_minimum: Mapped[bool] = mapped_column(Boolean, nullable=False)
    model_name: Mapped[str] = mapped_column(String(30), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')",
            name="check_pred_blood_group",
        ),
        CheckConstraint("predicted_stock >= 0", name="check_pred_stock_non_negative"),
        UniqueConstraint("run_id", "blood_group", "forecast_date", name="uq_run_group_date"),
    )
