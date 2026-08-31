from unittest.mock import MagicMock, patch

from backend.ai_service import AIRecoveryRecommendation
from datetime import datetime

from backend.database import Base
from backend.models import (
    AuditLog,
    Customer,
    Invoice,
    PaymentAttempt,
)
from backend.recovery_service import (
    create_ai_recovery_attempt,
    create_recovery_attempt,
    record_recovery_outcome,
)

from tests.test_database_config import (
    TestSessionLocal,
    test_engine,
)

@patch("backend.recovery_service.analyze_payment_failure")
def test_create_ai_recovery_attempt_uses_guardrail(
    mock_analyze_payment_failure,
):
    # Start with a clean test database.
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
            razorpay_payment_id="pay_ai_test_001",
            status="failed",
            failure_reason="insufficient_funds",
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        # Gemini recommends retry_payment.
        # The deterministic policy for insufficient_funds
        # only permits PAYMENT_EXTENSION, so the guardrail
        # must override Gemini.
        mock_analyze_payment_failure.return_value = (
            AIRecoveryRecommendation(
                recommendation="retry_payment",
                explanation="Retry may recover the payment.",
                confidence=0.91,
            )
        )

        recovery = create_ai_recovery_attempt(
            db=db,
            payment_attempt=payment,
        )

        assert recovery.id is not None

        # Guardrail should reject Gemini's incompatible
        # recommendation.
        assert recovery.strategy == "PAYMENT_EXTENSION"
        assert recovery.status == "planned"
        assert recovery.amount_recovered == 0.0

        assert (
            "not compatible with the recovery policy"
            in recovery.notes
        )

        # Verify AI audit event.
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_id == str(invoice.id),
                AuditLog.event_type == "AI_RECOVERY_DECISION",
            )
            .first()
        )

        assert audit is not None
        assert "retry_payment" in audit.message
        assert "PAYMENT_EXTENSION" in audit.message

        mock_analyze_payment_failure.assert_called_once()

    finally:
        db.close()


def test_create_recovery_attempt_from_failed_payment():
    # Start with a completely clean test database.
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()

    try:
        # Create test customer
        customer = Customer(
            customer_id="RECOVERY-TEST-CUST-001",
            name="Recovery Test Customer",
            email="recovery-test@example.com",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        # Create test invoice
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

        # Create failed payment
        payment = PaymentAttempt(
            invoice_id=invoice.id,
            razorpay_payment_id="pay_recovery_test_001",
            status="failed",
            failure_reason="insufficient_funds",
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        # Create recovery attempt
        recovery = create_recovery_attempt(
            db=db,
            payment_attempt=payment,
        )

        # Verify recovery attempt
        assert recovery.id is not None
        assert recovery.invoice_id == invoice.id
        assert recovery.strategy == "PAYMENT_EXTENSION"
        assert recovery.status == "planned"
        assert recovery.amount_recovered == 0.0
        assert "5" in recovery.notes

        # Verify audit log was created
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_id == str(invoice.id),
                AuditLog.event_type == "RECOVERY_DECISION",
            )
            .first()
        )

        assert audit is not None
        assert audit.entity_type == "invoice"
        assert "PAYMENT_EXTENSION" in audit.message

    finally:
        db.close()
def test_record_recovery_outcome():
    # Start with a clean test database.
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()

    try:
        customer = Customer(
            customer_id="OUTCOME-TEST-CUST-001",
            name="Outcome Test Customer",
            email="outcome-test@example.com",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        invoice = Invoice(
            invoice_id="OUTCOME-TEST-INV-001",
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
            razorpay_payment_id="pay_outcome_test_001",
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

        updated = record_recovery_outcome(
            db=db,
            recovery_attempt=recovery,
            status="completed",
            amount_recovered=10000.0,
            notes="Demo recovery succeeded.",
        )

        assert updated.status == "completed"
        assert updated.amount_recovered == 10000.0
        assert "Demo recovery succeeded." in updated.notes

        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_id == str(invoice.id),
                AuditLog.event_type == "RECOVERY_OUTCOME",
            )
            .first()
        )

        assert audit is not None
        assert "10000.00" in audit.message

    finally:
        db.close()
@patch("backend.recovery_service.analyze_payment_failure")
def test_create_ai_recovery_attempt_accepts_compatible_recommendation(
    mock_analyze_payment_failure,
):
    # Start with a clean test database.
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()

    try:
        customer = Customer(
            customer_id="AI-TEST-CUST-002",
            name="AI Compatible Customer",
            email="ai-compatible@example.com",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        invoice = Invoice(
            invoice_id="AI-TEST-INV-002",
            customer_id=customer.id,
            amount=15000.0,
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
            failure_reason="card_expired",
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        # Gemini recommends the same strategy as the
        # deterministic policy.
        mock_analyze_payment_failure.return_value = (
            AIRecoveryRecommendation(
                recommendation="payment_method_update",
                explanation="The customer should update the expired card.",
                confidence=0.95,
            )
        )

        recovery = create_ai_recovery_attempt(
            db=db,
            payment_attempt=payment,
        )

        assert recovery.id is not None
        assert recovery.strategy == "PAYMENT_METHOD_UPDATE"
        assert recovery.status == "planned"
        assert recovery.amount_recovered == 0.0

        assert "AI recommendation accepted" in recovery.notes
        assert "0.95" in recovery.notes

        # Verify the AI decision was recorded.
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_id == str(invoice.id),
                AuditLog.event_type == "AI_RECOVERY_DECISION",
            )
            .first()
        )

        assert audit is not None
        assert "payment_method_update" in audit.message
        assert "PAYMENT_METHOD_UPDATE" in audit.message

        mock_analyze_payment_failure.assert_called_once()

    finally:
        db.close()