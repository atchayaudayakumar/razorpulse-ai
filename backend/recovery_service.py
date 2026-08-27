from sqlalchemy.orm import Session

from backend.audit_service import create_audit_log
from backend.models import PaymentAttempt, RecoveryAttempt
from backend.recovery_engine import decide_recovery_strategy


def create_recovery_attempt(
    db: Session,
    payment_attempt: PaymentAttempt,
) -> RecoveryAttempt:
    decision = decide_recovery_strategy(
        payment_attempt.failure_reason or ""
    )

    recovery_attempt = RecoveryAttempt(
        invoice_id=payment_attempt.invoice_id,
        strategy=decision.strategy,
        status="planned",
        amount_recovered=0.0,
        notes=(
            f"{decision.reason} "
            f"Extension days: {decision.extension_days}. "
            f"Discount: {decision.discount_percent}%."
        ),
    )

    db.add(recovery_attempt)
    db.commit()
    db.refresh(recovery_attempt)

    create_audit_log(
        db=db,
        event_type="RECOVERY_DECISION",
        entity_type="invoice",
        entity_id=str(payment_attempt.invoice_id),
        message=(
            f"Strategy: {decision.strategy}. "
            f"Reason: {decision.reason}. "
            f"Extension days: {decision.extension_days}. "
            f"Discount: {decision.discount_percent}%."
        ),
    )

    return recovery_attempt