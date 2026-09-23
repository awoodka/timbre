from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UsageCounter(Base):
    """How many times something happened on one UTC day, for the daily allowances in
    services/quota.py. `subject` is "user:<id>", "ip:<address>" or "all" (site-wide)."""

    __tablename__ = "usage_counters"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    subject: Mapped[str] = mapped_column(String(80), primary_key=True)
    action: Mapped[str] = mapped_column(String(20), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
