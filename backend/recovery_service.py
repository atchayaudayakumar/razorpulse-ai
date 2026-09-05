from sqlalchemy.orm import Session

from backend.ai_service import analyze_payment_failure
from backend.audit_service import create_audit_log
from backend.models import Customer, Invoice, PaymentAttempt, RecoveryAttempt
from backend.recovery_engine import decide_recovery_strategy
from backend.risk_service import calculate_payment_risk


# ==========================================================
# RECOVERY GUARDRAILS
# ==========================================================

MAX_RECOVERY_ATTEMPTS = 3


# ==========================================================
# RECOVERY ATTEMPT COUNT
# ==========================================================

def get_recovery_attempt_count(
    db: Session,
    invoice_id: int,
) -> int:
    """
    Return the number of recovery attempts already created
    for an invoice.
    """

    return (
        db.query(RecoveryAttempt)
        .filter(
            RecoveryAttempt.invoice_id == invoice_id
        )
        .count()
    )


def can_retry_recovery(
    db: Session,
    invoice_id: int,
) -> bool:
    """
    Determine whether another recovery attempt is allowed.

    RazorPulse allows a maximum of three recovery attempts
    for the same invoice.
    """

    return (
        get_recovery_attempt_count(
            db=db,
            invoice_id=invoice_id,
        )
        < MAX_RECOVERY_ATTEMPTS
    )


# ==========================================================
# DETERMINISTIC RECOVERY
# ==========================================================

def create_recovery_attempt(
    db: Session,
    payment_attempt: PaymentAttempt,
) -> RecoveryAttempt:
    """
    Create a deterministic recovery attempt.

    The deterministic recovery engine decides the strategy.
    Recovery attempts are bounded by MAX_RECOVERY_ATTEMPTS.
    """

    # ------------------------------------------------------
    # STOP RULE
    # ------------------------------------------------------

    if not can_retry_recovery(
        db=db,
        invoice_id=payment_attempt.invoice_id,
    ):
        raise ValueError(
            "Maximum recovery attempts reached. "
            "Recovery has been stopped and requires manual review."
        )

    # ------------------------------------------------------
    # DECISION
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # AUDIT DECISION
    # ------------------------------------------------------

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


# ==========================================================
# AI RECOVERY
# ==========================================================

def create_ai_recovery_attempt(
    db: Session,
    payment_attempt: PaymentAttempt,
) -> RecoveryAttempt:
    """
    Create an AI-assisted recovery attempt.

    Gemini provides the recommendation.

    RazorPulse deterministic guardrails remain authoritative,
    meaning an AI recommendation cannot bypass the recovery
    policy.
    """

    # ------------------------------------------------------
    # STOP RULE
    # ------------------------------------------------------

    if not can_retry_recovery(
        db=db,
        invoice_id=payment_attempt.invoice_id,
    ):
        raise ValueError(
            "Maximum recovery attempts reached. "
            "Recovery has been stopped and requires manual review."
        )

    # ------------------------------------------------------
    # LOAD INVOICE
    # ------------------------------------------------------

    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.id == payment_attempt.invoice_id
        )
        .first()
    )

    if invoice is None:
        raise ValueError(
            f"Invoice {payment_attempt.invoice_id} not found."
        )

    # ------------------------------------------------------
    # LOAD CUSTOMER
    # ------------------------------------------------------

    customer = (
        db.query(Customer)
        .filter(
            Customer.id == invoice.customer_id
        )
        .first()
    )

    if customer is None:
        raise ValueError(
            f"Customer for invoice {invoice.invoice_id} not found."
        )

    # ------------------------------------------------------
    # CALCULATE RISK
    # ------------------------------------------------------

    risk = calculate_payment_risk(
        db=db,
        payment_attempt=payment_attempt,
    )

    # ------------------------------------------------------
    # AI ANALYSIS
    # ------------------------------------------------------

    ai_recommendation = analyze_payment_failure(
        customer_name=customer.name,
        invoice_amount=invoice.amount,
        failure_reason=payment_attempt.failure_reason or "",
        risk_level=risk.risk_level,
    )

    # ------------------------------------------------------
    # DETERMINISTIC POLICY
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # AI GUARDRAIL
    # ------------------------------------------------------

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
            f"AI recommendation "
            f"'{ai_recommendation.recommendation}' "
            f"was not compatible with the recovery policy. "
            f"Deterministic guardrail selected "
            f"{deterministic_decision.strategy}. "
            f"AI confidence: "
            f"{ai_recommendation.confidence:.2f}. "
            f"AI explanation: "
            f"{ai_recommendation.explanation}"
        )

    # ------------------------------------------------------
    # CREATE RECOVERY ATTEMPT
    # ------------------------------------------------------

    recovery_attempt = RecoveryAttempt(
        invoice_id=invoice.id,
        strategy=final_strategy,
        status="planned",
        amount_recovered=0.0,
        notes=(
            f"{final_reason} "
            f"Extension days: "
            f"{deterministic_decision.extension_days}. "
            f"Discount: "
            f"{deterministic_decision.discount_percent}%."
        ),
    )

    db.add(recovery_attempt)
    db.commit()
    db.refresh(recovery_attempt)

    # ------------------------------------------------------
    # AUDIT AI DECISION
    # ------------------------------------------------------

    create_audit_log(
        db=db,
        event_type="AI_RECOVERY_DECISION",
        entity_type="invoice",
        entity_id=str(invoice.id),
        message=(
            f"AI recommendation: "
            f"{ai_recommendation.recommendation}. "
            f"Confidence: "
            f"{ai_recommendation.confidence:.2f}. "
            f"Final strategy: "
            f"{final_strategy}. "
            f"Risk level: "
            f"{risk.risk_level}."
        ),
    )

    return recovery_attempt


# ==========================================================
# RECORD RECOVERY OUTCOME
# ==========================================================

def record_recovery_outcome(
    db: Session,
    recovery_attempt: RecoveryAttempt,
    status: str,
    amount_recovered: float,
    notes: str = "",
) -> RecoveryAttempt:
    """
    Record the outcome of an existing recovery attempt.

    This function preserves the original RECOVERY_OUTCOME
    audit event and adds the bounded recovery-loop events.

    Recovery lifecycle:

        planned
           ↓
        completed
           → stop

        failed
           ↓
        retry allowed
           ↓
        failed again
           ↓
        maximum attempts
           ↓
        manual review / stop
    """

    # ------------------------------------------------------
    # VALIDATE STATUS
    # ------------------------------------------------------

    allowed_statuses = {
        "completed",
        "failed",
        "manual_review",
    }

    if status not in allowed_statuses:
        raise ValueError(
            f"Invalid recovery status: {status}"
        )

    # ------------------------------------------------------
    # VALIDATE AMOUNT
    # ------------------------------------------------------

    if amount_recovered < 0:
        raise ValueError(
            "amount_recovered cannot be negative."
        )

    # ------------------------------------------------------
    # UPDATE RECOVERY ATTEMPT
    # ------------------------------------------------------

    recovery_attempt.status = status
    recovery_attempt.amount_recovered = amount_recovered

    if notes:
        existing_notes = recovery_attempt.notes or ""

        recovery_attempt.notes = (
            f"{existing_notes} "
            f"Outcome: {notes}"
        ).strip()

    db.commit()
    db.refresh(recovery_attempt)

    # ------------------------------------------------------
    # ALWAYS CREATE THE ORIGINAL OUTCOME AUDIT EVENT
    # ------------------------------------------------------
    #
    # IMPORTANT:
    # Existing tests and the application rely on this event.
    # Do not replace it with the newer loop-specific events.
    #

    create_audit_log(
        db=db,
        event_type="RECOVERY_OUTCOME",
        entity_type="invoice",
        entity_id=str(recovery_attempt.invoice_id),
        message=(
            f"Recovery outcome: {status}. "
            f"Amount recovered: "
            f"₹{amount_recovered:.2f}. "
            f"Notes: {notes}"
        ),
    )

    # ------------------------------------------------------
    # SUCCESS → STOP
    # ------------------------------------------------------

    if status == "completed":

        create_audit_log(
            db=db,
            event_type="RECOVERY_COMPLETED",
            entity_type="invoice",
            entity_id=str(recovery_attempt.invoice_id),
            message=(
                f"Recovery completed successfully. "
                f"₹{amount_recovered:.2f} recovered. "
                f"No further recovery attempts required."
            ),
        )

        return recovery_attempt

    # ------------------------------------------------------
    # MANUAL REVIEW → STOP
    # ------------------------------------------------------

    if status == "manual_review":

        create_audit_log(
            db=db,
            event_type="RECOVERY_MANUAL_REVIEW",
            entity_type="invoice",
            entity_id=str(recovery_attempt.invoice_id),
            message=(
                "Recovery requires manual review. "
                "Automated recovery has stopped."
            ),
        )

        return recovery_attempt

    # ------------------------------------------------------
    # FAILED → CHECK RETRY LIMIT
    # ------------------------------------------------------

    attempt_count = get_recovery_attempt_count(
        db=db,
        invoice_id=recovery_attempt.invoice_id,
    )

    # ------------------------------------------------------
    # MAXIMUM ATTEMPTS REACHED
    # ------------------------------------------------------

    if attempt_count >= MAX_RECOVERY_ATTEMPTS:

        # Convert the current failed attempt into a
        # manual-review state so the database clearly
        # communicates that automation has stopped.

        recovery_attempt.status = "manual_review"

        existing_notes = recovery_attempt.notes or ""

        stop_note = (
            f"Maximum recovery attempts reached "
            f"({MAX_RECOVERY_ATTEMPTS}). "
            f"Automated recovery stopped; "
            f"manual review required."
        )

        recovery_attempt.notes = (
            f"{existing_notes} {stop_note}"
        ).strip()

        db.commit()
        db.refresh(recovery_attempt)

        create_audit_log(
            db=db,
            event_type="RECOVERY_STOPPED",
            entity_type="invoice",
            entity_id=str(recovery_attempt.invoice_id),
            message=(
                f"Recovery stopped after "
                f"{attempt_count} attempts. "
                f"Maximum allowed attempts: "
                f"{MAX_RECOVERY_ATTEMPTS}. "
                f"Manual review required."
            ),
        )

        return recovery_attempt

    # ------------------------------------------------------
    # FAILED BUT RETRY IS STILL ALLOWED
    # ------------------------------------------------------

    remaining_attempts = (
        MAX_RECOVERY_ATTEMPTS - attempt_count
    )

    create_audit_log(
        db=db,
        event_type="RECOVERY_RETRY_ALLOWED",
        entity_type="invoice",
        entity_id=str(recovery_attempt.invoice_id),
        message=(
            f"Recovery attempt failed. "
            f"Retry is allowed. "
            f"Attempts used: {attempt_count}. "
            f"Remaining attempts: {remaining_attempts}."
        ),
    )

    return recovery_attempt