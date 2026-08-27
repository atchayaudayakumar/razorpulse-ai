import pytest

from backend.razorpay_service import get_razorpay_client


def test_razorpay_client_requires_credentials(monkeypatch):
    monkeypatch.setattr(
        "backend.razorpay_service.RAZORPAY_KEY_ID",
        "",
    )

    monkeypatch.setattr(
        "backend.razorpay_service.RAZORPAY_KEY_SECRET",
        "",
    )

    with pytest.raises(ValueError):
        get_razorpay_client()