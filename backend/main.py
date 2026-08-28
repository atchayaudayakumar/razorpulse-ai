from backend.database import Base, engine, SessionLocal
from backend.models import Invoice
from backend.payment_service import record_payment_attempt
from backend.risk_service import calculate_payment_risk
from backend.recovery_service import create_ai_recovery_attempt
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

    payload = await request.json()

    if payload.get("event") != "payment.failed":
        return {
            "status": "ignored",
            "reason": "Unsupported event.",
        }

    payment_entity = (
        payload
        .get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )

    razorpay_payment_id = payment_entity.get("id")
    razorpay_order_id = payment_entity.get("order_id")
    status = payment_entity.get("status", "")
    error_description = payment_entity.get(
        "error_description",
        "",
    )

    if not razorpay_payment_id or not razorpay_order_id:
        raise HTTPException(
            status_code=400,
            detail="Payment ID or order ID is missing.",
        )

    db = SessionLocal()

    try:
        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.razorpay_order_id
                == razorpay_order_id
            )
            .first()
        )

        if invoice is None:
            raise HTTPException(
                status_code=404,
                detail="Invoice for Razorpay order not found.",
            )

        payment_attempt = record_payment_attempt(
            db=db,
            invoice_id=invoice.id,
            status=status,
            razorpay_payment_id=razorpay_payment_id,
            failure_reason=error_description,
        )

        risk = calculate_payment_risk(
            db=db,
            payment_attempt=payment_attempt,
        )

        recovery = create_ai_recovery_attempt(
            db=db,
            payment_attempt=payment_attempt,
        )

        return {
            "status": "processed",
            "payment_id": razorpay_payment_id,
            "invoice_id": invoice.id,
            "risk_level": risk.risk_level,
            "risk_score": risk.risk_score,
            "revenue_at_risk": risk.revenue_at_risk,
            "recovery_strategy": recovery.strategy,
        }

    finally:
        db.close()
   