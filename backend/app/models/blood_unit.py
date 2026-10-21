from datetime import date
from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class BloodUnit(Base):
    __tablename__ = "blood_units"

    unit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    donor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("donors.donor_id", ondelete="RESTRICT"), nullable=False
    )
    blood_group: Mapped[str] = mapped_column(String(3), nullable=False)
    collection_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="available")

    __table_args__ = (
        CheckConstraint(
            "blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')",
            name="check_unit_blood_group",
        ),
        CheckConstraint(
            "status IN ('available', 'issued', 'expired')",
            name="check_unit_status",
        ),
        CheckConstraint("expiry_date > collection_date", name="check_unit_expiry_after_collection"),
    )

    donor: Mapped["Donor"] = relationship("Donor", back_populates="blood_units")
    issue_record: Mapped["IssueRecord"] = relationship("IssueRecord", back_populates="unit", uselist=False)
