from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import CheckConstraint, Date, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Donor(Base):
    __tablename__ = "donors"

    donor_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    blood_group: Mapped[str] = mapped_column(String(3), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    last_donation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    __table_args__ = (
        CheckConstraint("gender IN ('male', 'female', 'other')", name="check_donor_gender"),
        CheckConstraint(
            "blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')",
            name="check_donor_blood_group",
        ),
        CheckConstraint("weight > 0", name="check_donor_weight_positive"),
    )

    blood_units: Mapped[list["BloodUnit"]] = relationship("BloodUnit", back_populates="donor")
