from datetime import UTC, datetime

from app.models import (
    ExecutedAction,
    ExecutionStatus,
)
from app.state import CaseState
from app.verification.service import (
    _matched_invoice_ids,
)


def test_extracts_successfully_matched_invoice_ids() -> None:
    state = CaseState(
        customer_id="ACME",
        description="Billing issue.",
        executed_actions=[
            ExecutedAction(
                tool_name="match_payment",
                arguments={
                    "customer_id": "ACME",
                    "payment_id": "TX-9912",
                    "invoice_id": "INV-8231",
                },
                status=(
                    ExecutionStatus.SUCCESS
                ),
                started_at=datetime.now(
                    UTC
                ),
                completed_at=datetime.now(
                    UTC
                ),
            )
        ],
    )

    assert (
        _matched_invoice_ids(state)
        == ["INV-8231"]
    )