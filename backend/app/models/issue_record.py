from datetime import date
from sqlalchemy import Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class IssueRecord(Base):
    __tablename__ = "issue_records"

    issue_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("blood_requests.request_id", ondelete="RESTRICT"), nullable=False
    )
    unit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("blood_units.unit_id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    issued_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("staff.staff_id", ondelete="RESTRICT"), nullable=False
    )

    request: Mapped["BloodRequest"] = relationship("BloodRequest", back_populates="issue_records")
    unit: Mapped["BloodUnit"] = relationship("BloodUnit", back_populates="issue_record")
    staff_member: Mapped["Staff"] = relationship("Staff", back_populates="issued_records")
