from datetime import datetime
import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from backend.config import RAZORPAY_WEBHOOK_SECRET
from backend.database import Base
from backend.models import Customer, Invoice
from backend.main import app
import backend.main

from tests.test_database_config import (
    TestSessionLocal,
    test_engine,
)


client = TestClient(app)

backend.main.SessionLocal = TestSessionLocal

def test_valid_razorpay_webhook_is_accepted():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()

    try:
        customer = Customer(
            customer_id="WEBHOOK-TEST-CUST-001",
            name="Webhook Test Customer",
            email="webhook-test@example.com",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        invoice = Invoice(
            invoice_id="WEBHOOK-TEST-INV-001",
            razorpay_order_id="order_test_123",
            customer_id=customer.id,
            amount=10000.0,
            currency="INR",
            status="pending",
            due_date=datetime.utcnow(),
        )

        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        payload = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_123",
                        "order_id": "order_test_123",
                        "status": "failed",
                        "error_description": "Insufficient funds",
                    }
                }
            },
        }

        body = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode()

        signature = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()

        response = client.post(
            "/webhooks/razorpay",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": signature,
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "processed"
        assert response.json()["payment_id"] == "pay_test_123"
        assert response.json()["invoice_id"] == invoice.id

    finally:
        db.close()


def test_invalid_razorpay_webhook_is_rejected():
    payload = {
        "event": "payment.failed",
    }

    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    signature = "invalid-signature"

    response = client.post(
        "/webhooks/razorpay",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature,
        },
    )

    assert response.status_code == 400