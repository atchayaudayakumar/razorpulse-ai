from sqlalchemy.orm import Session

from backend.models import Invoice, PaymentAttempt
from backend.risk_engine import RevenueRisk, calculate_revenue_risk


def calculate_payment_risk(
    db: Session,
    payment_attempt: PaymentAttempt,
) -> RevenueRisk:
    """
    Calculate revenue risk for a real PaymentAttempt
    using the associated Invoice.
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

    return calculate_revenue_risk(
        invoice_amount=invoice.amount,
        payment_status=payment_attempt.status,
        failure_reason=payment_attempt.failure_reason,
    )