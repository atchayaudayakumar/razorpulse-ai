import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from backend.config import RAZORPAY_WEBHOOK_SECRET
from backend.main import app


client = TestClient(app)


def test_valid_razorpay_webhook_is_accepted():
    payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_123",
                    "status": "failed",
                    "error_description": "Insufficient funds",
                }
            }
        },
    }

    # Create the exact JSON body that will be sent.
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
    assert response.json()["status"] == "received"


def test_invalid_razorpay_webhook_is_rejected():
    payload = {
        "event": "payment.failed",
    }

    response = client.post(
        "/webhooks/razorpay",
        json=payload,
        headers={
            "X-Razorpay-Signature": "invalid-signature",
        },
    )

    assert response.status_code == 400