from backend.ai_service import (
    AIRecoveryRecommendation,
)


def test_ai_recovery_recommendation_structure():
    recommendation = AIRecoveryRecommendation(
        recommendation="payment_extension",
        explanation="Customer may have a temporary cash-flow issue.",
        confidence=0.87,
    )

    assert recommendation.recommendation == "payment_extension"
    assert recommendation.confidence == 0.87
    assert "cash-flow" in recommendation.explanation


def test_ai_recommendation_can_require_manual_review():
    recommendation = AIRecoveryRecommendation(
        recommendation="manual_review",
        explanation="The failure reason is unclear.",
        confidence=0.40,
    )

    assert recommendation.recommendation == "manual_review"
    assert recommendation.confidence == 0.40