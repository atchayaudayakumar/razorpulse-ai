from backend.risk_engine import calculate_revenue_risk


def test_failed_payment_creates_revenue_risk():
    risk = calculate_revenue_risk(
        invoice_amount=10000.0,
        payment_status="failed",
        failure_reason="insufficient_funds",
    )

    assert risk.risk_score == 65.0
    assert risk.risk_level == "MEDIUM"
    assert risk.revenue_at_risk == 10000.0


def test_expired_card_is_high_risk():
    risk = calculate_revenue_risk(
        invoice_amount=25000.0,
        payment_status="failed",
        failure_reason="card_expired",
    )

    assert risk.risk_score == 70.0
    assert risk.risk_level == "HIGH"
    assert risk.revenue_at_risk == 25000.0


def test_successful_payment_has_no_revenue_risk():
    risk = calculate_revenue_risk(
        invoice_amount=15000.0,
        payment_status="success",
        failure_reason=None,
    )

    assert risk.risk_score == 0.0
    assert risk.risk_level == "LOW"
    assert risk.revenue_at_risk == 0.0