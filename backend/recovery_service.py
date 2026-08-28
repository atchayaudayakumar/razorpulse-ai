from sqlalchemy.orm import Session

from backend.ai_service import analyze_payment_failure
from backend.audit_service import create_audit_log
from backend.models import Customer, Invoice, PaymentAttempt, RecoveryAttempt
from backend.recovery_engine import decide_recovery_strategy
from backend.risk_service import calculate_payment_risk


def create_recovery_attempt(
    db: Session,
    payment_attempt: PaymentAttempt,
) -> RecoveryAttempt:
    """
    Create a deterministic recovery attempt.

    This remains the original rule-based recovery path.
    """

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


def create_ai_recovery_attempt(
    db: Session,
    payment_attempt: PaymentAttempt,
) -> RecoveryAttempt:
    """
    Create an AI-assisted recovery attempt.

    Gemini provides a recommendation.
    RazorPulse guardrails determine whether that recommendation
    is compatible with the deterministic recovery policy.
    """

    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == payment_attempt.invoice_id)
        .first()
    )

    if invoice is None:
        raise ValueError(
            f"Invoice {payment_attempt.invoice_id} not found."
        )

    customer = (
        db.query(Customer)
        .filter(Customer.id == invoice.customer_id)
        .first()
    )

    if customer is None:
        raise ValueError(
            f"Customer for invoice {invoice.invoice_id} not found."
        )

    risk = calculate_payment_risk(
        db=db,
        payment_attempt=payment_attempt,
    )

    ai_recommendation = analyze_payment_failure(
        customer_name=customer.name,
        invoice_amount=invoice.amount,
        failure_reason=payment_attempt.failure_reason or "",
        risk_level=risk.risk_level,
    )

    deterministic_decision = decide_recovery_strategy(
        payment_attempt.failure_reason or ""
    )

    strategy_map = {
        "retry_payment": "RETRY_PAYMENT",
        "payment_method_update": "PAYMENT_METHOD_UPDATE",
        "payment_extension": "PAYMENT_EXTENSION",
        "manual_review": "MANUAL_REVIEW",
    }

    ai_strategy = strategy_map.get(
        ai_recommendation.recommendation
    )

    # Gemini must agree with the deterministic policy.
    # Otherwise, use the safe deterministic decision.
    if ai_strategy == deterministic_decision.strategy:
        final_strategy = ai_strategy
        final_reason = (
            f"AI recommendation accepted. "
            f"Confidence: {ai_recommendation.confidence:.2f}. "
            f"{ai_recommendation.explanation}"
        )
    else:
        final_strategy = deterministic_decision.strategy
        final_reason = (
            f"AI recommendation '{ai_recommendation.recommendation}' "
            f"was not compatible with the recovery policy. "
            f"Deterministic guardrail selected "
            f"{deterministic_decision.strategy}. "
            f"AI confidence: {ai_recommendation.confidence:.2f}. "
            f"AI explanation: {ai_recommendation.explanation}"
        )

    recovery_attempt = RecoveryAttempt(
        invoice_id=invoice.id,
        strategy=final_strategy,
        status="planned",
        amount_recovered=0.0,
        notes=(
            f"{final_reason} "
            f"Extension days: {deterministic_decision.extension_days}. "
            f"Discount: {deterministic_decision.discount_percent}%."
        ),
    )

    db.add(recovery_attempt)
    db.commit()
    db.refresh(recovery_attempt)

    create_audit_log(
        db=db,
        event_type="AI_RECOVERY_DECISION",
        entity_type="invoice",
        entity_id=str(invoice.id),
        message=(
            f"AI recommendation: "
            f"{ai_recommendation.recommendation}. "
            f"Confidence: {ai_recommendation.confidence:.2f}. "
            f"Final strategy: {final_strategy}. "
            f"Risk level: {risk.risk_level}."
        ),
    )

    return recovery_attempt