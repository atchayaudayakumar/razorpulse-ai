from dataclasses import dataclass

from google import genai

from backend.config import GEMINI_API_KEY


@dataclass
class AIRecoveryRecommendation:
    recommendation: str
    explanation: str
    confidence: float


def analyze_payment_failure(
    customer_name: str,
    invoice_amount: float,
    failure_reason: str,
    risk_level: str,
) -> AIRecoveryRecommendation:
    """
    Ask Gemini to analyze a failed payment and recommend
    an appropriate recovery strategy.

    Gemini recommends.
    RazorPulse guardrails decide what is actually allowed.
    """

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key="AQ.Ab8RN6I7y71igKQuLVbYf6rZBb8NMcEI5x06-RPK1nKMixYTQg")

    prompt = f"""
You are the AI analysis component of RazorPulse,
an AI-assisted revenue recovery system.

Analyze this failed payment:

Customer: {customer_name}
Invoice amount: ₹{invoice_amount:.2f}
Failure reason: {failure_reason}
Risk level: {risk_level}

Choose ONE recovery strategy from:

- retry_payment
- payment_method_update
- payment_extension
- manual_review

Return exactly:

RECOMMENDATION: <strategy>
CONFIDENCE: <number between 0 and 1>
EXPLANATION: <short explanation>

Do not invent customer information.
Do not recommend discounts.
Do not perform any payment action.
Only provide analysis and a recommendation.
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
    )

    text = interaction.output_text.strip()

    recommendation = "manual_review"
    confidence = 0.0
    explanation = text

    for line in text.splitlines():
        line = line.strip()

        if line.startswith("RECOMMENDATION:"):
            recommendation = line.split(":", 1)[1].strip()

        elif line.startswith("CONFIDENCE:"):
            try:
                confidence = float(
                    line.split(":", 1)[1].strip()
                )
            except ValueError:
                confidence = 0.0

        elif line.startswith("EXPLANATION:"):
            explanation = line.split(":", 1)[1].strip()

    allowed_recommendations = {
        "retry_payment",
        "payment_method_update",
        "payment_extension",
        "manual_review",
    }

    if recommendation not in allowed_recommendations:
        recommendation = "manual_review"

    confidence = max(0.0, min(confidence, 1.0))

    return AIRecoveryRecommendation(
        recommendation=recommendation,
        explanation=explanation,
        confidence=confidence,
    )