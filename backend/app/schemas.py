import uuid
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import BookingStatus


# ---------- Bookings: public ----------

class BookingCreate(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=120)
    phone: str = Field(..., min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    pickup_location: str = Field(..., min_length=2, max_length=255)
    drop_location: str = Field(..., min_length=2, max_length=255)
    goods_type: str = Field(..., min_length=2, max_length=255)
    preferred_date: Optional[date] = None
    notes: Optional[str] = None


class BookingCreated(BaseModel):
    tracking_code: str
    status: BookingStatus
    message: str = "Booking received. Save your tracking code to check status."


class TrackingRequest(BaseModel):
    tracking_code: str
    phone: str


class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: BookingStatus
    note: Optional[str] = None
    changed_by: str
    changed_at: datetime


class BookingPublicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tracking_code: str
    status: BookingStatus
    pickup_location: str
    drop_location: str
    goods_type: str
    preferred_date: Optional[date] = None
    created_at: datetime
    history: List[StatusHistoryOut] = []


# ---------- Bookings: admin ----------

class BookingAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tracking_code: str
    customer_name: str
    phone: str
    email: Optional[str] = None
    pickup_location: str
    drop_location: str
    goods_type: str
    preferred_date: Optional[date] = None
    notes: Optional[str] = None
    status: BookingStatus
    created_at: datetime
    updated_at: datetime


class BookingAdminDetailOut(BookingAdminOut):
    history: List[StatusHistoryOut] = []


class StatusUpdate(BaseModel):
    status: BookingStatus
    note: Optional[str] = None
    notify_customer: bool = True


# ---------- Auth ----------

class AdminLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: str
    full_name: str
