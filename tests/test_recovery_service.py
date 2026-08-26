from datetime import datetime

from backend.database import Base
from backend.models import Customer, Invoice, PaymentAttempt
from backend.recovery_service import create_recovery_attempt

from tests.test_database_config import (
    TestSessionLocal,
    test_engine,
)


def test_create_recovery_attempt_from_failed_payment():
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()

    try:
        customer = Customer(
            customer_id="RECOVERY-TEST-CUST-001",
            name="Recovery Test Customer",
            email="recovery-test@example.com",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        invoice = Invoice(
            invoice_id="RECOVERY-TEST-INV-001",
            customer_id=customer.id,
            amount=10000.0,
            currency="INR",
            status="pending",
            due_date=datetime.utcnow(),
        )

        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        payment = PaymentAttempt(
            invoice_id=invoice.id,
            razorpay_payment_id="pay_recovery_test_001",
            status="failed",
            failure_reason="insufficient_funds",
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        recovery = create_recovery_attempt(
            db=db,
            payment_attempt=payment,
        )

        assert recovery.id is not None
        assert recovery.invoice_id == invoice.id
        assert recovery.strategy == "PAYMENT_EXTENSION"
        assert recovery.status == "planned"
        assert recovery.amount_recovered == 0.0
        assert "5" in recovery.notes

    finally:
        db.close()