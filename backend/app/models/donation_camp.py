from datetime import date
from sqlalchemy import CheckConstraint, Date, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class DonationCamp(Base):
    __tablename__ = "donation_camps"

    camp_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    location: Mapped[str] = mapped_column(Text, nullable=False)
    camp_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_units: Mapped[int] = mapped_column(Integer, nullable=False)
    units_collected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("target_units > 0", name="check_camp_target_units_positive"),
        CheckConstraint("units_collected >= 0", name="check_camp_units_collected_non_negative"),
    )
