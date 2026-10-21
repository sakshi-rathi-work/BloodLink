from datetime import date
from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class BloodRequest(Base):
    __tablename__ = "blood_requests"

    request_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requester_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("requesters.requester_id", ondelete="RESTRICT"), nullable=False
    )
    blood_group: Mapped[str] = mapped_column(String(3), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    urgency: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="pending")
    request_date: Mapped[date] = mapped_column(Date, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')",
            name="check_request_blood_group",
        ),
        CheckConstraint("quantity >= 1", name="check_request_quantity_min"),
        CheckConstraint("urgency IN ('emergency', 'routine')", name="check_request_urgency"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'issued', 'rejected')",
            name="check_request_status",
        ),
    )

    requester: Mapped["Requester"] = relationship("Requester", back_populates="requests")
    issue_records: Mapped[list["IssueRecord"]] = relationship("IssueRecord", back_populates="request")
