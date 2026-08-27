from backend.audit_service import create_audit_log
from backend.database import Base

from tests.test_database_config import (
    TestSessionLocal,
    test_engine,
)


def test_create_audit_log():
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()

    try:
        audit = create_audit_log(
            db=db,
            event_type="RECOVERY_DECISION",
            entity_type="invoice",
            entity_id="TEST-INV-001",
            message="Selected 5-day payment extension.",
        )

        assert audit.id is not None
        assert audit.event_type == "RECOVERY_DECISION"
        assert audit.entity_type == "invoice"
        assert audit.entity_id == "TEST-INV-001"
        assert "5-day" in audit.message

    finally:
        db.close()