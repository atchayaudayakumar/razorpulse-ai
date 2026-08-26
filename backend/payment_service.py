from sqlalchemy.orm import Session

from backend.models import PaymentAttempt


def record_payment_attempt(
    db: Session,
    invoice_id: int,
    status: str,
    razorpay_payment_id: str | None = None,
    failure_reason: str | None = None,
) -> PaymentAttempt:
    payment_attempt = PaymentAttempt(
        invoice_id=invoice_id,
        razorpay_payment_id=razorpay_payment_id,
        status=status,
        failure_reason=failure_reason,
    )

    db.add(payment_attempt)
    db.commit()
    db.refresh(payment_attempt)

    return payment_attempt