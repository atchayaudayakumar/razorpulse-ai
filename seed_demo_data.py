from datetime import datetime, timedelta

from backend.database import Base, SessionLocal, engine
from backend.models import (
    AuditLog,
    Customer,
    Invoice,
    PaymentAttempt,
    RecoveryAttempt,
)
from backend.recovery_engine import decide_recovery_strategy
from backend.recovery_service import record_recovery_outcome


DEMO_CUSTOMERS = [
    {
        "customer_id": "DEMO-CUST-001",
        "name": "Ananya Stores",
        "email": "ananya.demo@example.com",
        "invoice_id": "DEMO-INV-001",
        "razorpay_order_id": "order_demo_001",
        "amount": 25000.0,
        "failure_reason": "insufficient_funds",
        "payment_id": "pay_demo_001",
        "outcome": "completed",
        "amount_recovered": 25000.0,
        "outcome_notes": "Customer paid after the payment extension.",
    },
    {
        "customer_id": "DEMO-CUST-002",
        "name": "Bharat Tech",
        "email": "bharat.demo@example.com",
        "invoice_id": "DEMO-INV-002",
        "razorpay_order_id": "order_demo_002",
        "amount": 45000.0,
        "failure_reason": "card_expired",
        "payment_id": "pay_demo_002",
        "outcome": "completed",
        "amount_recovered": 45000.0,
        "outcome_notes": "Customer updated the payment method successfully.",
    },
    {
        "customer_id": "DEMO-CUST-003",
        "name": "Cauvery Foods",
        "email": "cauvery.demo@example.com",
        "invoice_id": "DEMO-INV-003",
        "razorpay_order_id": "order_demo_003",
        "amount": 12000.0,
        "failure_reason": "payment_declined",
        "payment_id": "pay_demo_003",
        "outcome": "failed",
        "amount_recovered": 0.0,
        "outcome_notes": "Controlled retry was unsuccessful.",
    },
    {
        "customer_id": "DEMO-CUST-004",
        "name": "Delta Services",
        "email": "delta.demo@example.com",
        "invoice_id": "DEMO-INV-004",
        "razorpay_order_id": "order_demo_004",
        "amount": 75000.0,
        "failure_reason": "unknown_failure",
        "payment_id": "pay_demo_004",
        "outcome": "manual_review",
        "amount_recovered": 0.0,
        "outcome_notes": "Automatic recovery stopped and requires manual review.",
    },
    {
        "customer_id": "DEMO-CUST-005",
        "name": "Erode Retail",
        "email": "erode.demo@example.com",
        "invoice_id": "DEMO-INV-005",
        "razorpay_order_id": "order_demo_005",
        "amount": 18000.0,
        "failure_reason": None,
        "payment_id": "pay_demo_005",
    },
]


def seed_demo_data():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        for data in DEMO_CUSTOMERS:

            # --------------------------------------------------
            # Customer
            # --------------------------------------------------

            customer = (
                db.query(Customer)
                .filter(
                    Customer.customer_id
                    == data["customer_id"]
                )
                .first()
            )

            if customer is None:
                customer = Customer(
                    customer_id=data["customer_id"],
                    name=data["name"],
                    email=data["email"],
                )
                db.add(customer)
                db.flush()

            # --------------------------------------------------
            # Invoice
            # --------------------------------------------------

            invoice = (
                db.query(Invoice)
                .filter(
                    Invoice.invoice_id
                    == data["invoice_id"]
                )
                .first()
            )

            if invoice is None:
                invoice = Invoice(
                    invoice_id=data["invoice_id"],
                    razorpay_order_id=data["razorpay_order_id"],
                    customer_id=customer.id,
                    amount=data["amount"],
                    currency="INR",
                    status="pending",
                    due_date=datetime.utcnow()
                    + timedelta(days=7),
                )
                db.add(invoice)
                db.flush()

            # --------------------------------------------------
            # Payment attempt
            # --------------------------------------------------

            payment = (
                db.query(PaymentAttempt)
                .filter(
                    PaymentAttempt.razorpay_payment_id
                    == data["payment_id"]
                )
                .first()
            )

            if payment is None:

                payment_status = (
                    "success"
                    if data["failure_reason"] is None
                    else "failed"
                )

                payment = PaymentAttempt(
                    invoice_id=invoice.id,
                    razorpay_payment_id=data["payment_id"],
                    status=payment_status,
                    failure_reason=data["failure_reason"],
                )

                db.add(payment)
                db.flush()

            # --------------------------------------------------
            # Recovery + audit
            # --------------------------------------------------

            if (
                data["failure_reason"] is not None
                and payment.status == "failed"
            ):

                recovery = (
                    db.query(RecoveryAttempt)
                    .filter(
                        RecoveryAttempt.invoice_id
                        == invoice.id
                    )
                    .first()
                )

                if recovery is None:

                    decision = decide_recovery_strategy(
                        data["failure_reason"]
                    )

                    recovery = RecoveryAttempt(
                        invoice_id=invoice.id,
                        strategy=decision.strategy,
                        status="planned",
                        amount_recovered=0.0,
                        notes=(
                            f"{decision.reason} "
                            f"Extension days: "
                            f"{decision.extension_days}. "
                            f"Discount: "
                            f"{decision.discount_percent}%."
                        ),
                    )

                    db.add(recovery)
                    db.commit()
                    db.refresh(recovery)

                    create_decision_audit = AuditLog(
                        event_type="RECOVERY_DECISION",
                        entity_type="invoice",
                        entity_id=str(invoice.id),
                        message=(
                            f"Demo recovery decision. "
                            f"Strategy: {decision.strategy}. "
                            f"Reason: {decision.reason}. "
                            f"Extension days: "
                            f"{decision.extension_days}. "
                            f"Discount: "
                            f"{decision.discount_percent}%."
                        ),
                    )

                    db.add(create_decision_audit)
                    db.commit()

                # --------------------------------------------------
                # Record the demo recovery outcome once
                # --------------------------------------------------

                existing_outcome = (
                    db.query(AuditLog)
                    .filter(
                        AuditLog.entity_type == "invoice",
                        AuditLog.entity_id == str(invoice.id),
                        AuditLog.event_type == "RECOVERY_OUTCOME",
                    )
                    .first()
                )

                if existing_outcome is None:

                    record_recovery_outcome(
                        db=db,
                        recovery_attempt=recovery,
                        status=data["outcome"],
                        amount_recovered=data["amount_recovered"],
                        notes=data["outcome_notes"],
                    )

        print("Demo data seeded successfully.")

        print(
            f"Customers: {db.query(Customer).count()}"
        )
        print(
            f"Invoices: {db.query(Invoice).count()}"
        )
        print(
            "PaymentAttempts: "
            f"{db.query(PaymentAttempt).count()}"
        )
        print(
            "RecoveryAttempts: "
            f"{db.query(RecoveryAttempt).count()}"
        )
        print(
            f"AuditLogs: {db.query(AuditLog).count()}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()