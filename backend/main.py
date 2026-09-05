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
    Customer,
    Invoice,
    PaymentAttempt,
    RecoveryAttempt,
)
from backend.risk_service import calculate_payment_risk
from backend.ai_service import analyze_payment_failure
from backend.recovery_service import (
    create_ai_recovery_attempt,
    create_recovery_attempt,
    record_recovery_outcome,
)


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

Base.metadata.create_all(bind=engine)


# ==========================================================
# FASTAPI APPLICATION
# ==========================================================

app = FastAPI(
    title=APP_NAME,
    description="AI-powered revenue recovery agent",
    version="0.1.0",
)


# ==========================================================
# REQUEST MODELS
# ==========================================================

class RecoveryRequest(BaseModel):
    mode: Literal["deterministic", "ai"] = "deterministic"

class AIInsightsRequest(BaseModel):
    customer_name: str
    invoice_amount: float
    failure_reason: str
    risk_level: str
# ==========================================================
# BASIC ENDPOINTS
# ==========================================================

@app.get("/")
def root():
    return {
        "app": APP_NAME,
        "environment": APP_ENV,
        "running": True,
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# ==========================================================
# RAZORPAY WEBHOOK
# ==========================================================

@app.post("/webhooks/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None),
):
    body = await request.body()

    # Webhook secret must be configured.
    if not RAZORPAY_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Razorpay webhook secret is not configured",
        )

    # Signature is mandatory.
    if not x_razorpay_signature:
        raise HTTPException(
            status_code=400,
            detail="Missing Razorpay signature",
        )

    # Calculate expected Razorpay signature.
    expected_signature = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    # Secure signature comparison.
    if not hmac.compare_digest(
        expected_signature,
        x_razorpay_signature,
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid Razorpay signature",
        )

    payload = await request.json()

    payment_entity = (
        payload
        .get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )

    razorpay_order_id = payment_entity.get("order_id")
    razorpay_payment_id = payment_entity.get("id")

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

        if not invoice:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found for Razorpay order",
            )

        # The test and existing API contract expect
        # the numeric database invoice ID here.
        return {
            "status": "processed",
            "payment_id": razorpay_payment_id,
            "invoice_id": invoice.id,
        }

    finally:
        db.close()


# ==========================================================
# FAILED PAYMENTS
# ==========================================================

@app.get("/api/failed-payments")
def get_failed_payments():
    db = SessionLocal()

    try:
        results = (
            db.query(
                PaymentAttempt,
                Invoice,
                Customer,
            )
            .join(
                Invoice,
                PaymentAttempt.invoice_id == Invoice.id,
            )
            .join(
                Customer,
                Invoice.customer_id == Customer.id,
            )
            .filter(
                PaymentAttempt.status == "failed"
            )
            .order_by(
                PaymentAttempt.attempted_at.desc()
            )
            .all()
        )

        return [
            {
                "payment_id": payment.razorpay_payment_id,
                "invoice_id": invoice.invoice_id,
                "customer": customer.name,
                "amount": invoice.amount,
                "currency": invoice.currency,
                "status": payment.status,
                "failure_reason": payment.failure_reason,
                "failed_at": payment.attempted_at,
            }
            for payment, invoice, customer in results
        ]

    finally:
        db.close()


# ==========================================================
# RECOVERY ATTEMPTS
# ==========================================================

@app.get("/api/recovery-attempts")
def get_recovery_attempts():
    db = SessionLocal()

    try:
        results = (
            db.query(
                RecoveryAttempt,
                Invoice,
            )
            .join(
                Invoice,
                RecoveryAttempt.invoice_id
                == Invoice.id,
            )
            .order_by(
                RecoveryAttempt.created_at.desc()
            )
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
            for recovery, invoice in results
        ]

    finally:
        db.close()


# ==========================================================
# CREATE RECOVERY ATTEMPT
# ==========================================================

@app.post("/api/recovery/{payment_id}")
def create_recovery(
    payment_id: str,
    recovery_request: RecoveryRequest,
):
    db = SessionLocal()

    try:
        payment = (
            db.query(PaymentAttempt)
            .filter(
                PaymentAttempt.razorpay_payment_id
                == payment_id
            )
            .first()
        )

        # Exact contract expected by tests.
        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment attempt not found.",
            )

        # Only failed payments can enter recovery.
        if payment.status != "failed":
            raise HTTPException(
                status_code=400,
                detail="Only failed payments can enter recovery.",
            )

        # Select recovery engine.
        if recovery_request.mode == "ai":
            recovery = create_ai_recovery_attempt(
                db,
                payment,
            )
        else:
            recovery = create_recovery_attempt(
                db,
                payment,
            )

        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.id == payment.invoice_id
            )
            .first()
        )

        if not invoice:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found",
            )

        # The recovery service already commits its
        # RecoveryAttempt. We refresh here for safety.
        db.refresh(recovery)

        return {
            "recovery_id": recovery.id,
            "payment_id": payment.razorpay_payment_id,
            "invoice_id": invoice.invoice_id,
            "mode": recovery_request.mode,
            "strategy": recovery.strategy,
            "status": recovery.status,
            "amount_recovered": recovery.amount_recovered,
            "notes": recovery.notes,
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    finally:
        db.close()


# ==========================================================
# UPDATE RECOVERY OUTCOME
# ==========================================================

@app.post("/api/recovery/{recovery_id}/outcome")
def update_recovery_outcome(
    recovery_id: int,
    status: str,
    amount_recovered: float = 0.0,
    notes: str = "",
):
    # Validate status before touching the database.
    valid_statuses = {
        "completed",
        "failed",
        "manual_review",
    }

    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid recovery status.",
        )

    # Validate amount before touching the database.
    if amount_recovered < 0:
        raise HTTPException(
            status_code=400,
            detail="amount_recovered cannot be negative.",
        )

    db = SessionLocal()

    try:
        recovery = (
            db.query(RecoveryAttempt)
            .filter(
                RecoveryAttempt.id == recovery_id
            )
            .first()
        )

        # Exact contract expected by tests.
        if not recovery:
            raise HTTPException(
                status_code=404,
                detail="Recovery attempt not found.",
            )

        # IMPORTANT:
        # record_recovery_outcome() expects the
        # RecoveryAttempt object, not recovery_id.
        updated_recovery = record_recovery_outcome(
            db=db,
            recovery_attempt=recovery,
            status=status,
            amount_recovered=amount_recovered,
            notes=notes,
        )

        return {
            "recovery_id": updated_recovery.id,
            "status": updated_recovery.status,
            "amount_recovered": updated_recovery.amount_recovered,
            "notes": updated_recovery.notes,
        }

    except HTTPException:
        db.rollback()
        raise

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    finally:
        db.close()


# ==========================================================
# RISK ANALYSIS
# ==========================================================

@app.get("/api/risk-analysis")
def get_risk_analysis():
    db = SessionLocal()

    try:
        results = (
            db.query(
                PaymentAttempt,
                Invoice,
            )
            .join(
                Invoice,
                PaymentAttempt.invoice_id
                == Invoice.id,
            )
            .order_by(
                PaymentAttempt.attempted_at.desc()
            )
            .all()
        )

        response = []

        for payment, invoice in results:
            risk = calculate_payment_risk(
                db,
                payment,
            )

            response.append(
                {
                    "payment_id": payment.razorpay_payment_id,
                    "invoice_id": invoice.invoice_id,
                    "risk_score": risk.risk_score,
                    "risk_level": risk.risk_level,
                    "revenue_at_risk": risk.revenue_at_risk,
                    "reason": risk.reason,
                }
            )

        return response

    finally:
        db.close()

# ==========================================================
# AI INSIGHTS
# ==========================================================

@app.post("/api/ai-insights")
def get_ai_insights(
    request: AIInsightsRequest,
):
    try:
        result = analyze_payment_failure(
            customer_name=request.customer_name,
            invoice_amount=request.invoice_amount,
            failure_reason=request.failure_reason,
            risk_level=request.risk_level,
        )

        return {
            "recommendation": result.recommendation,
            "explanation": result.explanation,
            "confidence": result.confidence,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {exc}",
        )

# ==========================================================
# AUDIT LOGS
# ==========================================================

@app.get("/api/audit-logs")
def get_audit_logs():
    db = SessionLocal()

    try:
        logs = (
            db.query(AuditLog)
            .order_by(
                AuditLog.created_at.desc()
            )
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