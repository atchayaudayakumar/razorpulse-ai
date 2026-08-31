import hashlib
import hmac

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from typing import Literal
from sqlalchemy.orm import Session

from backend.config import (
    APP_ENV,
    APP_NAME,
    RAZORPAY_WEBHOOK_SECRET,
)
from backend.database import Base, SessionLocal, engine
from backend.models import (
    AuditLog,
    Invoice,
    PaymentAttempt,
    RecoveryAttempt,
)

from backend.risk_service import calculate_payment_risk
from backend.recovery_service import record_recovery_outcome
from backend.recovery_service import (
    create_ai_recovery_attempt,
    create_recovery_attempt,
)
# Create all database tables defined in models.py
Base.metadata.create_all(bind=engine)


# Create the FastAPI application
app = FastAPI(
    title=APP_NAME,
    description="AI-powered revenue recovery agent",
    version="0.1.0",
)

class RecoveryRequest(BaseModel):
    mode: Literal["deterministic", "ai"] = "deterministic"
# ---------------------------------------------------------
# Root
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "app": APP_NAME,
        "environment": APP_ENV,
        "status": "running",
    }


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# ---------------------------------------------------------
# Razorpay Webhook
# ---------------------------------------------------------
@app.post("/webhooks/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default=""),
):
    """
    Receive and verify Razorpay webhook events.
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

    payment_entity = (
        payload
        .get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )

    payment_id = payment_entity.get("id")
    order_id = payment_entity.get("order_id")

    db = SessionLocal()

    try:
        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.razorpay_order_id == order_id
            )
            .first()
        )

        if invoice is None:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found for Razorpay order.",
            )

        return {
            "status": "processed",
            "payment_id": payment_id,
            "invoice_id": invoice.id,
        }

    finally:
        db.close()
# ---------------------------------------------------------
# Failed Payments API
# ---------------------------------------------------------

@app.get("/api/failed-payments")
def get_failed_payments():
    """
    Return failed payment attempts from the database.
    """

    db: Session = SessionLocal()

    try:
        payments = (
            db.query(PaymentAttempt)
            .filter(PaymentAttempt.status == "failed")
            .order_by(PaymentAttempt.attempted_at.desc())
            .all()
        )

        results = []

        for payment in payments:
            results.append(
                {
                    "payment_id": payment.razorpay_payment_id,
                    "invoice_id": payment.invoice_id,
                    "status": payment.status,
                    "failure_reason": payment.failure_reason,
                    "attempted_at": payment.attempted_at,
                }
            )

        return results

    finally:
        db.close()


# ---------------------------------------------------------
# Recovery Attempts API
# ---------------------------------------------------------

@app.get("/api/recovery-attempts")
def get_recovery_attempts():
    """
    Return recovery attempts together with invoice information.
    """

    db: Session = SessionLocal()

    try:
        attempts = (
            db.query(RecoveryAttempt, Invoice)
            .join(
                Invoice,
                RecoveryAttempt.invoice_id == Invoice.id,
            )
            .order_by(RecoveryAttempt.id.desc())
            .all()
        )

        return [
            {
                "recovery_id": recovery.id,
                "invoice_id": invoice.invoice_id,
                "amount": invoice.amount,
                "currency": invoice.currency,
                "strategy": recovery.strategy,
                "status": recovery.status,
                "amount_recovered": recovery.amount_recovered,
                "notes": recovery.notes,
            }
            for recovery, invoice in attempts
        ]

    finally:
        db.close()

# ---------------------------------------------------------
# Recovery Action API
# ---------------------------------------------------------

@app.post("/api/recovery/{payment_id}")
def trigger_recovery(
    payment_id: str,
    recovery_request: RecoveryRequest,
):
    """
    Trigger a controlled recovery decision for a failed payment.

    AI mode allows Gemini to recommend a strategy, but the
    deterministic recovery policy remains the final guardrail.
    """

    db: Session = SessionLocal()

    try:
        payment = (
            db.query(PaymentAttempt)
            .filter(
                PaymentAttempt.razorpay_payment_id == payment_id
            )
            .first()
        )

        if payment is None:
            raise HTTPException(
                status_code=404,
                detail="Payment attempt not found.",
            )

        if payment.status != "failed":
            raise HTTPException(
                status_code=400,
                detail="Only failed payments can enter recovery.",
            )

        if recovery_request.mode == "ai":
            recovery = create_ai_recovery_attempt(
                db=db,
                payment_attempt=payment,
            )
        else:
            recovery = create_recovery_attempt(
                db=db,
                payment_attempt=payment,
            )

        return {
            "recovery_id": recovery.id,
            "payment_id": payment.razorpay_payment_id,
            "invoice_id": recovery.invoice_id,
            "mode": recovery_request.mode,
            "strategy": recovery.strategy,
            "status": recovery.status,
            "amount_recovered": recovery.amount_recovered,
            "notes": recovery.notes,
        }

    finally:
        db.close()

# ---------------------------------------------------------
# Recovery Outcome API
# ---------------------------------------------------------

@app.post("/api/recovery/{recovery_id}/outcome")
def update_recovery_outcome(
    recovery_id: int,
    status: str,
    amount_recovered: float = 0.0,
    notes: str = "",
):
    """
    Record the result of a recovery attempt.
    """

    db: Session = SessionLocal()

    try:
        recovery = (
            db.query(RecoveryAttempt)
            .filter(RecoveryAttempt.id == recovery_id)
            .first()
        )

        if recovery is None:
            raise HTTPException(
                status_code=404,
                detail="Recovery attempt not found.",
            )

        if status not in {
            "completed",
            "failed",
            "manual_review",
        }:
            raise HTTPException(
                status_code=400,
                detail="Invalid recovery status.",
            )

        if amount_recovered < 0:
            raise HTTPException(
                status_code=400,
                detail="amount_recovered cannot be negative.",
            )

        recovery = record_recovery_outcome(
            db=db,
            recovery_attempt=recovery,
            status=status,
            amount_recovered=amount_recovered,
            notes=notes,
        )

        return {
            "recovery_id": recovery.id,
            "invoice_id": recovery.invoice_id,
            "strategy": recovery.strategy,
            "status": recovery.status,
            "amount_recovered": recovery.amount_recovered,
            "notes": recovery.notes,
        }

    finally:
        db.close()
# ---------------------------------------------------------
# Risk Analysis API
# ---------------------------------------------------------

@app.get("/api/risk-analysis")
def get_risk_analysis():
    """
    Calculate revenue risk for every payment attempt
    using the existing risk service and risk engine.
    """

    db: Session = SessionLocal()

    try:
        payments = (
            db.query(PaymentAttempt)
            .order_by(PaymentAttempt.attempted_at.desc())
            .all()
        )

        results = []

        for payment in payments:
            risk = calculate_payment_risk(
                db,
                payment,
            )

            results.append(
                {
                    "payment_id": payment.razorpay_payment_id,
                    "invoice_id": payment.invoice_id,
                    "risk_score": risk.risk_score,
                    "risk_level": risk.risk_level,
                    "revenue_at_risk": risk.revenue_at_risk,
                    "reason": risk.reason,
                }
            )

        return results


    finally:
        db.close()



# ---------------------------------------------------------
# Audit Trail API
# ---------------------------------------------------------

@app.get("/api/audit-logs")
def get_audit_logs():
    """
    Return audit logs ordered from newest to oldest.
    """

    db: Session = SessionLocal()

    try:
        logs = (
            db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .all()
        )

        return [
            {
                "id": log.id,
                "event_type": log.event_type,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "message": log.message,
                "created_at": log.created_at,
            }
            for log in logs
        ]

    finally:
         db.close()