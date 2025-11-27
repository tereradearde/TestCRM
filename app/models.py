from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Operator(Base):
    __tablename__ = "operators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    load_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="operator")
    assignments: Mapped[list["SourceOperatorAssignment"]] = relationship(
        "SourceOperatorAssignment", back_populates="operator", cascade="all, delete-orphan"
    )


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="lead")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="source")
    assignments: Mapped[list["SourceOperatorAssignment"]] = relationship(
        "SourceOperatorAssignment", back_populates="source", cascade="all, delete-orphan"
    )


class SourceOperatorAssignment(Base):
    __tablename__ = "source_operator_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    operator_id: Mapped[int] = mapped_column(ForeignKey("operators.id", ondelete="CASCADE"), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)

    source: Mapped["Source"] = relationship("Source", back_populates="assignments")
    operator: Mapped["Operator"] = relationship("Operator", back_populates="assignments")

    __table_args__ = (
        UniqueConstraint("source_id", "operator_id", name="uq_source_operator"),
        CheckConstraint("weight > 0", name="ck_weight_positive"),
    )


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    operator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("operators.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    lead: Mapped["Lead"] = relationship("Lead", back_populates="contacts")
    source: Mapped["Source"] = relationship("Source", back_populates="contacts")
    operator: Mapped[Optional["Operator"]] = relationship("Operator", back_populates="contacts")


