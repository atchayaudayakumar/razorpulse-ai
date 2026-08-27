import hmac
import hashlib

from fastapi import FastAPI, Header, HTTPException, Request

from backend.config import (
    APP_NAME,
    APP_ENV,
    RAZORPAY_WEBHOOK_SECRET,
)
from backend.database import Base, engine
from backend import models


# Create all database tables defined in models.py
Base.metadata.create_all(bind=engine)


# Create the FastAPI application
app = FastAPI(
    title=APP_NAME,
    description="AI-powered revenue recovery agent",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "app": APP_NAME,
        "environment": APP_ENV,
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.post("/webhooks/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default=""),
):
    """
    Receive and verify Razorpay webhook events.

    Razorpay signs the raw request body using the webhook secret.
    """

    body = await request.body()

    if not RAZORPAY_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Razorpay webhook secret is not configured.",
        )

    expected_signature = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        expected_signature,
        x_razorpay_signature,
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook signature.",
        )

    return {
        "status": "received",
    }