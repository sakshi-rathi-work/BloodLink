from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Requester(Base):
    __tablename__ = "requesters"

    requester_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        CheckConstraint("type IN ('hospital', 'patient')", name="check_requester_type"),
    )

    user: Mapped["User"] = relationship("User", back_populates="requester_profile")
    requests: Mapped[list["BloodRequest"]] = relationship("BloodRequest", back_populates="requester")
