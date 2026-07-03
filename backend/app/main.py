import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, CORS_ORIGIN_LIST
from app.database import Base, engine
from app.routers import bookings, auth

logging.basicConfig(level=logging.INFO)

# Dev convenience only: creates tables if they don't exist yet.
# For production, use Alembic migrations instead (see README).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Booking, tracking, and status-notification API for Mother Teresa Transport.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGIN_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bookings.router)
app.include_router(auth.router)


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
