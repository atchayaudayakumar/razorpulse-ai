from datetime import datetime

from backend.database import Base
from backend.models import Customer, Invoice

from tests.test_database_config import (
    TestSessionLocal,
    test_engine,
)


def test_database_can_create_customer_and_invoice():
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()

    try:
        customer = Customer(
            customer_id="TEST-CUST-001",
            name="Test Customer",
            email="test@example.com",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        invoice = Invoice(
            invoice_id="TEST-INV-001",
            customer_id=customer.id,
            amount=10000.0,
            currency="INR",
            status="pending",
            due_date=datetime.utcnow(),
        )

        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        assert customer.id is not None
        assert invoice.id is not None
        assert invoice.customer_id == customer.id

    finally:
        db.close()