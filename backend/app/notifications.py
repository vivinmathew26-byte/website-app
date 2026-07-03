"""
Sends the customer an update whenever their booking is created or its status
changes. Email and WhatsApp/SMS are both optional and independently
configured via environment variables — if the relevant settings are blank,
the app just logs what *would* have been sent instead of failing, so it
works out of the box in development.

Wire up real credentials in .env:
  - SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD / SMTP_FROM
  - TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_WHATSAPP_FROM / TWILIO_SMS_FROM
"""
import logging
import smtplib
from email.message import EmailMessage

from app.config import settings
from app.models import Booking, BookingStatus

logger = logging.getLogger("notifications")

STATUS_MESSAGES = {
    BookingStatus.received: "We've received your booking request and will confirm shortly.",
    BookingStatus.confirmed: "Your booking is confirmed. A vehicle will be assigned soon.",
    BookingStatus.picked_up: "Your goods have been picked up.",
    BookingStatus.in_transit: "Your consignment is on the way.",
    BookingStatus.delivered: "Your consignment has been delivered. Thank you for choosing us!",
    BookingStatus.cancelled: "Your booking has been cancelled. Contact us if this is unexpected.",
}


def _compose_message(booking: Booking, note: str | None = None) -> str:
    base = STATUS_MESSAGES.get(booking.status, "Your booking status has been updated.")
    lines = [
        "Mother Teresa Transport",
        f"Tracking code: {booking.tracking_code}",
        base,
    ]
    if note:
        lines.append(f"Note: {note}")
    lines.append(f"Route: {booking.pickup_location} -> {booking.drop_location}")
    return "\n".join(lines)


def _send_email(to_email: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.info("[email disabled - no SMTP config] would send to %s: %s", to_email, body)
        return
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email
        msg.set_content(body)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Email sent to %s", to_email)
    except Exception:
        logger.exception("Failed to send email to %s", to_email)


def _send_whatsapp_or_sms(to_phone: str, body: str) -> None:
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.info("[whatsapp/sms disabled - no Twilio config] would send to %s: %s", to_phone, body)
        return
    try:
        from twilio.rest import Client  # imported lazily; only needed if configured

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        if settings.TWILIO_WHATSAPP_FROM:
            client.messages.create(
                from_=settings.TWILIO_WHATSAPP_FROM,
                to=f"whatsapp:{to_phone}",
                body=body,
            )
            logger.info("WhatsApp message sent to %s", to_phone)
        elif settings.TWILIO_SMS_FROM:
            client.messages.create(
                from_=settings.TWILIO_SMS_FROM,
                to=to_phone,
                body=body,
            )
            logger.info("SMS sent to %s", to_phone)
    except ImportError:
        logger.warning("twilio package not installed — run: pip install twilio")
    except Exception:
        logger.exception("Failed to send WhatsApp/SMS to %s", to_phone)


def notify_booking_update(booking: Booking, note: str | None = None) -> None:
    """Send an email and/or WhatsApp/SMS update for the booking's current status."""
    body = _compose_message(booking, note)

    if booking.email:
        subject = f"Booking {booking.tracking_code} — {booking.status.value.replace('_', ' ').title()}"
        _send_email(booking.email, subject, body)

    if booking.phone:
        _send_whatsapp_or_sms(booking.phone, body)
