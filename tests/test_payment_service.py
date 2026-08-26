from datetime import datetime

from backend.database import Base
from backend.models import Customer, Invoice
from backend.payment_service import record_payment_attempt

from tests.test_database_config import (
    TestSessionLocal,
    test_engine,
)


def test_record_failed_payment_attempt():
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()

    try:
        customer = Customer(
            customer_id="PAY-TEST-CUST-001",
            name="Payment Test Customer",
            email="payment-test@example.com",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        invoice = Invoice(
            invoice_id="PAY-TEST-INV-001",
            customer_id=customer.id,
            amount=10000.0,
            currency="INR",
            status="pending",
            due_date=datetime.utcnow(),
        )

        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        payment = record_payment_attempt(
            db=db,
            invoice_id=invoice.id,
            status="failed",
            razorpay_payment_id="pay_test_123",
            failure_reason="insufficient_funds",
        )

        assert payment.id is not None
        assert payment.invoice_id == invoice.id
        assert payment.status == "failed"
        assert payment.razorpay_payment_id == "pay_test_123"
        assert payment.failure_reason == "insufficient_funds"

    finally:
        db.close()