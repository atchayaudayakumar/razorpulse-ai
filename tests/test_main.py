from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.ai_service import AIRecoveryRecommendation
from backend.database import Base
from backend.main import app
from backend.models import Customer, Invoice, PaymentAttempt, RecoveryAttempt
from tests.test_database_config import TestSessionLocal, test_engine


client = TestClient(app)


def setup_test_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def create_test_payment(
    db,
    payment_id="pay_endpoint_test_001",
    status="failed",
    failure_reason="insufficient_funds",
):
    customer = Customer(
        customer_id=f"ENDPOINT-CUST-{payment_id}",
        name="Endpoint Test Customer",
        email="endpoint-test@example.com",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    invoice = Invoice(
        invoice_id=f"ENDPOINT-INV-{payment_id}",
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
        razorpay_payment_id=payment_id,
        status=status,
        failure_reason=failure_reason,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


def test_deterministic_recovery_endpoint():
    setup_test_database()

    db = TestSessionLocal()

    try:
        payment = create_test_payment(db)

        with patch("backend.main.SessionLocal", return_value=db):
            response = client.post(
                f"/api/recovery/{payment.razorpay_payment_id}",
                json={"mode": "deterministic"},
            )

        assert response.status_code == 200

        data = response.json()

        assert data["payment_id"] == payment.razorpay_payment_id
        assert data["mode"] == "deterministic"
        assert data["strategy"] == "PAYMENT_EXTENSION"
        assert data["status"] == "planned"
        assert data["amount_recovered"] == 0.0
        assert data["recovery_id"] is not None

        recovery = (
            db.query(RecoveryAttempt)
            .filter(RecoveryAttempt.id == data["recovery_id"])
            .first()
        )

        assert recovery is not None
        assert recovery.strategy == "PAYMENT_EXTENSION"

    finally:
        db.close()


def test_ai_recovery_endpoint():
    setup_test_database()

    db = TestSessionLocal()

    try:
        payment = create_test_payment(
            db,
            payment_id="pay_endpoint_ai_001",
            failure_reason="insufficient_funds",
        )

        fake_ai_result = AIRecoveryRecommendation(
            recommendation="payment_extension",
            explanation="Temporary cash-flow issue is likely.",
            confidence=0.90,
        )

        with patch(
            "backend.main.SessionLocal",
            return_value=db,
        ), patch(
            "backend.recovery_service.analyze_payment_failure",
            return_value=fake_ai_result,
        ):
            response = client.post(
                f"/api/recovery/{payment.razorpay_payment_id}",
                json={"mode": "ai"},
            )

        assert response.status_code == 200

        data = response.json()

        assert data["payment_id"] == payment.razorpay_payment_id
        assert data["mode"] == "ai"
        assert data["strategy"] == "PAYMENT_EXTENSION"
        assert data["status"] == "planned"
        assert data["recovery_id"] is not None
        assert "AI recommendation accepted" in data["notes"]

    finally:
        db.close()


def test_ai_recovery_endpoint_respects_guardrail():
    setup_test_database()

    db = TestSessionLocal()

    try:
        payment = create_test_payment(
            db,
            payment_id="pay_endpoint_guardrail_001",
            failure_reason="insufficient_funds",
        )

        fake_ai_result = AIRecoveryRecommendation(
            recommendation="retry_payment",
            explanation="Retrying may recover the payment.",
            confidence=0.95,
        )

        with patch(
            "backend.main.SessionLocal",
            return_value=db,
        ), patch(
            "backend.recovery_service.analyze_payment_failure",
            return_value=fake_ai_result,
        ):
            response = client.post(
                f"/api/recovery/{payment.razorpay_payment_id}",
                json={"mode": "ai"},
            )

        assert response.status_code == 200

        data = response.json()

        assert data["strategy"] == "PAYMENT_EXTENSION"
        assert "was not compatible" in data["notes"]

    finally:
        db.close()


def test_recovery_endpoint_rejects_non_failed_payment():
    setup_test_database()

    db = TestSessionLocal()

    try:
        payment = create_test_payment(
            db,
            payment_id="pay_endpoint_success_001",
            status="success",
            failure_reason=None,
        )

        with patch("backend.main.SessionLocal", return_value=db):
            response = client.post(
                f"/api/recovery/{payment.razorpay_payment_id}",
                json={"mode": "deterministic"},
            )

        assert response.status_code == 400
        assert response.json()["detail"] == "Only failed payments can enter recovery."

    finally:
        db.close()


def test_recovery_endpoint_returns_404_for_unknown_payment():
    setup_test_database()

    db = TestSessionLocal()

    try:
        with patch("backend.main.SessionLocal", return_value=db):
            response = client.post(
                "/api/recovery/pay_does_not_exist",
                json={"mode": "deterministic"},
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Payment attempt not found."

    finally:
        db.close()


def test_recovery_endpoint_rejects_invalid_mode():
    setup_test_database()

    db = TestSessionLocal()

    try:
        payment = create_test_payment(
            db,
            payment_id="pay_endpoint_invalid_mode_001",
        )

        with patch("backend.main.SessionLocal", return_value=db):
            response = client.post(
                f"/api/recovery/{payment.razorpay_payment_id}",
                json={"mode": "something_invalid"},
            )

        assert response.status_code == 422

    finally:
        db.close()

def test_recovery_outcome_endpoint():
    setup_test_database()

    db = TestSessionLocal()

    try:
        payment = create_test_payment(db)

        recovery = RecoveryAttempt(
            invoice_id=payment.invoice_id,
            strategy="PAYMENT_EXTENSION",
            status="planned",
            amount_recovered=0.0,
        )

        db.add(recovery)
        db.commit()
        db.refresh(recovery)

        with patch("backend.main.SessionLocal", return_value=db):
            response = client.post(
                f"/api/recovery/{recovery.id}/outcome",
                params={
                    "status": "completed",
                    "amount_recovered": 5000,
                    "notes": "Payment recovered successfully.",
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["recovery_id"] == recovery.id
        assert data["status"] == "completed"
        assert data["amount_recovered"] == 5000.0

    finally:
        db.close()


def test_recovery_outcome_returns_404_for_unknown_recovery():
    setup_test_database()

    db = TestSessionLocal()

    try:
        with patch("backend.main.SessionLocal", return_value=db):
            response = client.post(
                "/api/recovery/9999/outcome",
                params={
                    "status": "completed",
                    "amount_recovered": 5000,
                },
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Recovery attempt not found."

    finally:
        db.close()


def test_recovery_outcome_rejects_invalid_status():
    setup_test_database()

    db = TestSessionLocal()

    try:
        payment = create_test_payment(db)

        recovery = RecoveryAttempt(
            invoice_id=payment.invoice_id,
            strategy="PAYMENT_EXTENSION",
            status="planned",
            amount_recovered=0.0,
        )

        db.add(recovery)
        db.commit()
        db.refresh(recovery)

        with patch("backend.main.SessionLocal", return_value=db):
            response = client.post(
                f"/api/recovery/{recovery.id}/outcome",
                params={
                    "status": "something_invalid",
                    "amount_recovered": 5000,
                },
            )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid recovery status."

    finally:
        db.close()


def test_recovery_outcome_rejects_negative_amount():
    setup_test_database()

    db = TestSessionLocal()

    try:
        payment = create_test_payment(db)

        recovery = RecoveryAttempt(
            invoice_id=payment.invoice_id,
            strategy="PAYMENT_EXTENSION",
            status="planned",
            amount_recovered=0.0,
        )

        db.add(recovery)
        db.commit()
        db.refresh(recovery)

        with patch("backend.main.SessionLocal", return_value=db):
            response = client.post(
                f"/api/recovery/{recovery.id}/outcome",
                params={
                    "status": "completed",
                    "amount_recovered": -100,
                },
            )

        assert response.status_code == 400
        assert response.json()["detail"] == "amount_recovered cannot be negative."

    finally:
        db.close()