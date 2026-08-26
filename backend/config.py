import os

from dotenv import load_dotenv


load_dotenv()


APP_NAME = os.getenv("APP_NAME", "RazorPulse")
APP_ENV = os.getenv("APP_ENV", "development")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./razorpulse.db",
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv(
    "RAZORPAY_WEBHOOK_SECRET",
)

MAX_DISCOUNT_PERCENT = float(
    os.getenv("MAX_DISCOUNT_PERCENT", "5")
)

MAX_EXTENSION_DAYS = int(
    os.getenv("MAX_EXTENSION_DAYS", "7")
)

MAX_CONTACT_ATTEMPTS = int(
    os.getenv("MAX_CONTACT_ATTEMPTS", "3")
)

MICRO_DOWNPAYMENT_PERCENT = float(
    os.getenv("MICRO_DOWNPAYMENT_PERCENT", "10")
)