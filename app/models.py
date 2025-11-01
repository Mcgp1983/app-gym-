from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )

    purchases: Mapped[list[Purchase]] = relationship(
        "Purchase", back_populates="member", cascade="all, delete-orphan"
    )


class MembershipPlan(Base):
    __tablename__ = "membership_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    purchases: Mapped[list[Purchase]] = relationship(
        "Purchase", back_populates="plan", cascade="all, delete-orphan"
    )


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("membership_plans.id"), nullable=False)
    start_date: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    access_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )

    member: Mapped[Member] = relationship("Member", back_populates="purchases")
    plan: Mapped[MembershipPlan] = relationship("MembershipPlan", back_populates="purchases")
    access_logs: Mapped[list[AccessLog]] = relationship(
        "AccessLog", back_populates="purchase", cascade="all, delete-orphan"
    )

    @staticmethod
    def generate_token() -> str:
        return uuid.uuid4().hex

    def is_active(self, reference: dt.datetime | None = None) -> bool:
        reference = reference or dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
        start = self.start_date
        end = self.end_date
        if start.tzinfo is None:
            start = start.replace(tzinfo=dt.timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=dt.timezone.utc)
        return start <= reference <= end


class AccessLog(Base):
    __tablename__ = "access_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id"), nullable=False)
    scanned_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255))

    purchase: Mapped[Purchase] = relationship("Purchase", back_populates="access_logs")
