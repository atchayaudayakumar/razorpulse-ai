from dataclasses import dataclass


@dataclass
class RevenueRisk:
    risk_score: float
    risk_level: str
    revenue_at_risk: float
    reason: str


def calculate_revenue_risk(
    invoice_amount: float,
    payment_status: str,
    failure_reason: str | None = None,
) -> RevenueRisk:
    """
    Calculate a deterministic revenue-risk score.

    Score:
        0-39   -> LOW
        40-69  -> MEDIUM
        70-100 -> HIGH
    """

    score = 0.0
    reasons = []

    status = payment_status.lower().strip()
    reason = (failure_reason or "").lower().strip()

    # No payment failure means there is currently no recovery risk.
    if status != "failed":
        return RevenueRisk(
            risk_score=0.0,
            risk_level="LOW",
            revenue_at_risk=0.0,
            reason="Payment is not currently marked as failed.",
        )

    # A failed payment creates a base risk.
    score += 50
    reasons.append("Payment failed.")

    # Different failure reasons have different recovery risk.
    if reason == "insufficient_funds":
        score += 15
        reasons.append("Insufficient funds may indicate a temporary cash-flow issue.")

    elif reason == "card_expired":
        score += 20
        reasons.append("The customer's payment method may need to be updated.")

    elif reason == "payment_declined":
        score += 10
        reasons.append("The payment may require a controlled retry.")

    else:
        score += 20
        reasons.append("Failure reason is unknown or requires further analysis.")

    # Keep the score within the defined range.
    score = min(score, 100.0)

    if score >= 70:
        risk_level = "HIGH"
    elif score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return RevenueRisk(
        risk_score=score,
        risk_level=risk_level,
        revenue_at_risk=float(invoice_amount),
        reason=" ".join(reasons),
    )