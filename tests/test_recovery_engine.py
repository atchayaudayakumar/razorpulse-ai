from backend.recovery_engine import decide_recovery_strategy


def test_insufficient_funds_gets_payment_extension():
    decision = decide_recovery_strategy(
        "insufficient_funds"
    )

    assert decision.strategy == "PAYMENT_EXTENSION"
    assert decision.extension_days == 5
    assert decision.discount_percent == 0.0


def test_expired_card_requires_payment_method_update():
    decision = decide_recovery_strategy(
        "card_expired"
    )

    assert decision.strategy == "PAYMENT_METHOD_UPDATE"
    assert decision.extension_days == 0
    assert decision.discount_percent == 0.0


def test_unknown_failure_requires_manual_review():
    decision = decide_recovery_strategy(
        "something_unknown"
    )

    assert decision.strategy == "MANUAL_REVIEW"
    assert decision.extension_days == 0
    assert decision.discount_percent == 0.0