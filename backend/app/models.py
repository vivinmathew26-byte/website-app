import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Enum as SAEnum, Date
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class BookingStatus(str, enum.Enum):
    received = "received"
    confirmed = "confirmed"
    picked_up = "picked_up"
    in_transit = "in_transit"
    delivered = "delivered"
    cancelled = "cancelled"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_code = Column(String(12), unique=True, nullable=False, index=True)

    customer_name = Column(String(120), nullable=False)
    phone = Column(String(20), nullable=False, index=True)
    email = Column(String(255), nullable=True)

    pickup_location = Column(String(255), nullable=False)
    drop_location = Column(String(255), nullable=False)
    goods_type = Column(String(255), nullable=False)
    preferred_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    status = Column(SAEnum(BookingStatus), nullable=False, default=BookingStatus.received)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    history = relationship(
        "BookingStatusHistory", back_populates="booking",
        order_by="BookingStatusHistory.changed_at", cascade="all, delete-orphan"
    )


class BookingStatusHistory(Base):
    __tablename__ = "booking_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)

    status = Column(SAEnum(BookingStatus), nullable=False)
    note = Column(Text, nullable=True)
    changed_by = Column(String(120), nullable=False, default="system")
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    booking = relationship("Booking", back_populates="history")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(80), unique=True, nullable=False, index=True)
    full_name = Column(String(120), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
