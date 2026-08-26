from dataclasses import dataclass

from backend.config import (
    MAX_DISCOUNT_PERCENT,
    MAX_EXTENSION_DAYS,
)


@dataclass
class RecoveryDecision:
    strategy: str
    extension_days: int
    discount_percent: float
    reason: str


def decide_recovery_strategy(
    failure_reason: str,
) -> RecoveryDecision:

    reason = failure_reason.lower().strip()

    if reason == "insufficient_funds":
        return RecoveryDecision(
            strategy="PAYMENT_EXTENSION",
            extension_days=min(5, MAX_EXTENSION_DAYS),
            discount_percent=0.0,
            reason="Customer appears to have a temporary cashflow constraint.",
        )

    if reason == "card_expired":
        return RecoveryDecision(
            strategy="PAYMENT_METHOD_UPDATE",
            extension_days=0,
            discount_percent=0.0,
            reason="Customer should update the expired payment method.",
        )

    if reason == "payment_declined":
        return RecoveryDecision(
            strategy="RETRY_PAYMENT",
            extension_days=1,
            discount_percent=0.0,
            reason="Payment may succeed on a controlled retry.",
        )

    return RecoveryDecision(
        strategy="MANUAL_REVIEW",
        extension_days=0,
        discount_percent=0.0,
        reason="Failure reason is not recognized by the recovery policy.",
    )