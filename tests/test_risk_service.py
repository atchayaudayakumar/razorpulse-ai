from datetime import datetime

from backend.database import Base
from backend.models import Customer, Invoice, PaymentAttempt
from backend.risk_service import calculate_payment_risk

from tests.test_database_config import (
    TestSessionLocal,
    test_engine,
)


def test_calculate_payment_risk_from_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()

    try:
        customer = Customer(
            customer_id="RISK-TEST-CUST-001",
            name="Risk Test Customer",
            email="risk-test@example.com",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        invoice = Invoice(
            invoice_id="RISK-TEST-INV-001",
            customer_id=customer.id,
            amount=20000.0,
            currency="INR",
            status="pending",
            due_date=datetime.utcnow(),
        )

        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        payment = PaymentAttempt(
            invoice_id=invoice.id,
            razorpay_payment_id="pay_risk_test_001",
            status="failed",
            failure_reason="insufficient_funds",
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        risk = calculate_payment_risk(
            db=db,
            payment_attempt=payment,
        )

        assert risk.risk_score == 65.0
        assert risk.risk_level == "MEDIUM"
        assert risk.revenue_at_risk == 20000.0
        assert "cash-flow" in risk.reason.lower()

    finally:
        db.close()