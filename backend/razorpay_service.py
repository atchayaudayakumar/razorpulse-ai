import razorpay

from backend.config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET


def get_razorpay_client():
    """
    Create and return a Razorpay API client.

    Credentials are loaded from environment variables
    through backend.config.
    """

    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise ValueError(
            "Razorpay API credentials are not configured."
        )

    return razorpay.Client(
        auth=(
            RAZORPAY_KEY_ID,
            RAZORPAY_KEY_SECRET,
        )
    )