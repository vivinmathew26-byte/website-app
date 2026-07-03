import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from sqlalchemy.orm import Session

from app import crud, schemas, models
from app.deps import get_db, get_current_admin
from app.notifications import notify_booking_update

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


# ============================================================
# Public endpoints — no login required
# ============================================================

@router.post("", response_model=schemas.BookingCreated, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: schemas.BookingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    booking = crud.create_booking(db, payload)
    background_tasks.add_task(notify_booking_update, booking, "Thanks for booking with us.")
    return schemas.BookingCreated(tracking_code=booking.tracking_code, status=booking.status)


@router.post("/track", response_model=schemas.BookingPublicOut)
def track_booking(payload: schemas.TrackingRequest, db: Session = Depends(get_db)):
    booking = crud.get_booking_by_tracking(db, payload.tracking_code, payload.phone)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No booking found for that tracking code and phone number.",
        )
    return booking


# ============================================================
# Admin endpoints — require a valid JWT (see app/routers/auth.py)
# ============================================================

@router.get("", response_model=list[schemas.BookingAdminOut])
def admin_list_bookings(
    status_filter: models.BookingStatus | None = Query(default=None, alias="status"),
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _admin: models.AdminUser = Depends(get_current_admin),
):
    return crud.list_bookings(db, status=status_filter, search=search, limit=limit, offset=offset)


@router.get("/{booking_id}", response_model=schemas.BookingAdminDetailOut)
def admin_get_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: models.AdminUser = Depends(get_current_admin),
):
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.patch("/{booking_id}/status", response_model=schemas.BookingAdminDetailOut)
def admin_update_status(
    booking_id: uuid.UUID,
    payload: schemas.StatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = crud.update_booking_status(
        db, booking, payload.status, payload.note, changed_by=admin.username
    )

    if payload.notify_customer:
        background_tasks.add_task(notify_booking_update, booking, payload.note)

    return booking
