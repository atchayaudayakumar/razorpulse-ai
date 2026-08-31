from unittest.mock import MagicMock, patch

from backend.ai_service import (
    AIRecoveryRecommendation,
    analyze_payment_failure,
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


@patch("backend.ai_service.genai.Client")
def test_analyze_payment_failure_parses_gemini_response(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    mock_interaction = MagicMock()
    mock_interaction.output_text = (
        "RECOMMENDATION: payment_extension\n"
        "CONFIDENCE: 0.87\n"
        "EXPLANATION: Customer may have a temporary cash-flow issue."
    )

    mock_client.interactions.create.return_value = mock_interaction

    result = analyze_payment_failure(
        customer_name="Test Customer",
        invoice_amount=10000.0,
        failure_reason="insufficient_funds",
        risk_level="HIGH",
    )

    assert result.recommendation == "payment_extension"
    assert result.confidence == 0.87
    assert "cash-flow" in result.explanation

    mock_client.interactions.create.assert_called_once()


@patch("backend.ai_service.genai.Client")
def test_analyze_payment_failure_invalid_recommendation_uses_manual_review(
    mock_client_class,
):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    mock_interaction = MagicMock()
    mock_interaction.output_text = (
        "RECOMMENDATION: give_free_money\n"
        "CONFIDENCE: 0.91\n"
        "EXPLANATION: Invalid recommendation."
    )

    mock_client.interactions.create.return_value = mock_interaction

    result = analyze_payment_failure(
        customer_name="Test Customer",
        invoice_amount=10000.0,
        failure_reason="unknown_failure",
        risk_level="HIGH",
    )

    assert result.recommendation == "manual_review"
    assert result.confidence == 0.91


@patch("backend.ai_service.genai.Client")
def test_analyze_payment_failure_clamps_confidence(
    mock_client_class,
):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    mock_interaction = MagicMock()
    mock_interaction.output_text = (
        "RECOMMENDATION: retry_payment\n"
        "CONFIDENCE: 2.5\n"
        "EXPLANATION: Retry may work."
    )

    mock_client.interactions.create.return_value = mock_interaction

    result = analyze_payment_failure(
        customer_name="Test Customer",
        invoice_amount=10000.0,
        failure_reason="payment_declined",
        risk_level="MEDIUM",
    )

    assert result.recommendation == "retry_payment"
    assert result.confidence == 1.0


@patch("backend.ai_service.genai.Client")
def test_analyze_payment_failure_malformed_confidence_defaults_to_zero(
    mock_client_class,
):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    mock_interaction = MagicMock()
    mock_interaction.output_text = (
        "RECOMMENDATION: manual_review\n"
        "CONFIDENCE: not-a-number\n"
        "EXPLANATION: Confidence could not be parsed."
    )

    mock_client.interactions.create.return_value = mock_interaction

    result = analyze_payment_failure(
        customer_name="Test Customer",
        invoice_amount=10000.0,
        failure_reason="unknown_failure",
        risk_level="HIGH",
    )

    assert result.recommendation == "manual_review"
    assert result.confidence == 0.0

def test_analyze_payment_failure_handles_gemini_failure():
    with patch(
        "backend.ai_service.genai.Client"
    ) as mock_client:
        mock_client.return_value.interactions.create.side_effect = (
            RuntimeError("Gemini API unavailable")
        )

        result = analyze_payment_failure(
            customer_name="Test Customer",
            invoice_amount=10000.0,
            failure_reason="insufficient_funds",
            risk_level="HIGH",
        )

    assert result.recommendation == "manual_review"
    assert result.confidence == 0.0
    assert "AI analysis was unavailable" in result.explanation


def test_analyze_payment_failure_handles_empty_gemini_response():
    with patch(
        "backend.ai_service.genai.Client"
    ) as mock_client:
        mock_client.return_value.interactions.create.return_value.output_text = ""

        result = analyze_payment_failure(
            customer_name="Test Customer",
            invoice_amount=10000.0,
            failure_reason="insufficient_funds",
            risk_level="HIGH",
        )

    assert result.recommendation == "manual_review"
    assert result.confidence == 0.0