from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from persistence.db import Base


class RiskAlertRecord(Base):
    __tablename__ = "risk_alerts"

    alert_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    alert_type: Mapped[str] = mapped_column(String(128), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    related_object_type: Mapped[str] = mapped_column(String(128), nullable=False)
    related_object_id: Mapped[str] = mapped_column(String(128), nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN")
    status_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    acknowledged_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    resolved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    dismissed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ActionResultRecord(Base):
    __tablename__ = "action_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_type: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    user: Mapped[str] = mapped_column(String(128), nullable=False)
    related_object_type: Mapped[str] = mapped_column(String(128), nullable=False)
    related_object_id: Mapped[str] = mapped_column(String(128), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")


class ReorderRequestRecord(Base):
    __tablename__ = "reorder_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    part_id: Mapped[str] = mapped_column(String(128), nullable=False)
    part_name: Mapped[str] = mapped_column(String(256), nullable=False)
    supplier_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    supplier_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    requested_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)