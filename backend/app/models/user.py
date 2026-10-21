from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'staff', 'requester')", name="check_user_role"),
    )

    staff_profile: Mapped["Staff"] = relationship("Staff", back_populates="user", uselist=False)
    requester_profile: Mapped["Requester"] = relationship("Requester", back_populates="user", uselist=False)
    activity_logs: Mapped[list["ActivityLog"]] = relationship("ActivityLog", back_populates="user")
