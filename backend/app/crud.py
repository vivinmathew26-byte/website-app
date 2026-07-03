import random
import string
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import select

from app import models, schemas


def _generate_tracking_code(db: Session) -> str:
    """MTT-XXXXXX, uppercase letters+digits, re-rolled on the rare collision."""
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "MTT-" + "".join(random.choices(alphabet, k=6))
        exists = db.query(models.Booking).filter(models.Booking.tracking_code == code).first()
        if not exists:
            return code


def create_booking(db: Session, data: schemas.BookingCreate) -> models.Booking:
    booking = models.Booking(
        tracking_code=_generate_tracking_code(db),
        customer_name=data.customer_name,
        phone=data.phone,
        email=data.email,
        pickup_location=data.pickup_location,
        drop_location=data.drop_location,
        goods_type=data.goods_type,
        preferred_date=data.preferred_date,
        notes=data.notes,
        status=models.BookingStatus.received,
    )
    db.add(booking)
    db.flush()

    db.add(models.BookingStatusHistory(
        booking_id=booking.id,
        status=models.BookingStatus.received,
        note="Booking created",
        changed_by="system",
    ))
    db.commit()
    db.refresh(booking)
    return booking


def get_booking_by_tracking(db: Session, tracking_code: str, phone: str) -> models.Booking | None:
    return (
        db.query(models.Booking)
        .filter(
            models.Booking.tracking_code == tracking_code.strip().upper(),
            models.Booking.phone == phone.strip(),
        )
        .first()
    )


def get_booking(db: Session, booking_id: uuid.UUID) -> models.Booking | None:
    return db.query(models.Booking).filter(models.Booking.id == booking_id).first()


def list_bookings(
    db: Session,
    status: models.BookingStatus | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    query = db.query(models.Booking)
    if status:
        query = query.filter(models.Booking.status == status)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (models.Booking.customer_name.ilike(like))
            | (models.Booking.phone.ilike(like))
            | (models.Booking.tracking_code.ilike(like))
            | (models.Booking.pickup_location.ilike(like))
            | (models.Booking.drop_location.ilike(like))
        )
    return (
        query.order_by(models.Booking.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def update_booking_status(
    db: Session,
    booking: models.Booking,
    new_status: models.BookingStatus,
    note: str | None,
    changed_by: str,
) -> models.Booking:
    booking.status = new_status
    db.add(models.BookingStatusHistory(
        booking_id=booking.id,
        status=new_status,
        note=note,
        changed_by=changed_by,
    ))
    db.commit()
    db.refresh(booking)
    return booking


def get_admin_by_username(db: Session, username: str) -> models.AdminUser | None:
    return db.query(models.AdminUser).filter(models.AdminUser.username == username).first()
