from datetime import datetime
from unittest.mock import patch

from backend.ai_service import AIRecoveryRecommendation
from backend.database import Base
from backend.models import Customer, Invoice, PaymentAttempt
from backend.recovery_service import create_ai_recovery_attempt

from tests.test_database_config import (
    TestSessionLocal,
    test_engine,
)


def test_ai_recovery_recommendation_is_accepted():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()

    try:
        customer = Customer(
            customer_id="AI-TEST-CUST-001",
            name="AI Test Customer",
            email="ai-test@example.com",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        invoice = Invoice(
            invoice_id="AI-TEST-INV-001",
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
            razorpay_payment_id="pay_ai_test_001",
            status="failed",
            failure_reason="insufficient_funds",
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        fake_ai_result = AIRecoveryRecommendation(
            recommendation="payment_extension",
            explanation="Temporary cash-flow issue is likely.",
            confidence=0.90,
        )

        with patch(
            "backend.recovery_service.analyze_payment_failure",
            return_value=fake_ai_result,
        ):
            recovery = create_ai_recovery_attempt(
                db=db,
                payment_attempt=payment,
            )

        assert recovery.id is not None
        assert recovery.strategy == "PAYMENT_EXTENSION"
        assert recovery.status == "planned"
        assert recovery.amount_recovered == 0.0
        assert "AI recommendation accepted" in recovery.notes
        assert "0.90" in recovery.notes

    finally:
        db.close()
def test_ai_recommendation_cannot_override_recovery_policy():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()

    try:
        customer = Customer(
            customer_id="AI-TEST-CUST-002",
            name="Guardrail Test Customer",
            email="guardrail-test@example.com",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        invoice = Invoice(
            invoice_id="AI-TEST-INV-002",
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
            razorpay_payment_id="pay_ai_test_002",
            status="failed",
            failure_reason="insufficient_funds",
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        fake_ai_result = AIRecoveryRecommendation(
            recommendation="retry_payment",
            explanation="Retrying may recover the payment.",
            confidence=0.95,
        )

        with patch(
            "backend.recovery_service.analyze_payment_failure",
            return_value=fake_ai_result,
        ):
            recovery = create_ai_recovery_attempt(
                db=db,
                payment_attempt=payment,
            )

        assert recovery.strategy == "PAYMENT_EXTENSION"
        assert "was not compatible" in recovery.notes
        assert "0.95" in recovery.notes

    finally:
        db.close()