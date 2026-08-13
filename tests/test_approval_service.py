from app.approvals.service import (
    compute_plan_digest,
)
from app.models import (
    PlannedAction,
    ResolutionPlan,
    RiskLevel,
)


def make_plan(
    invoice_id: str,
) -> ResolutionPlan:
    return ResolutionPlan(
        explanation="Resolve billing issue.",
        actions=[
            PlannedAction(
                tool_name="match_payment",
                arguments={
                    "customer_id": "ACME",
                    "payment_id": "TX-9912",
                    "invoice_id": invoice_id,
                },
                reason="Match payment.",
                evidence_ids=[
                    "E3",
                    "E4",
                ],
                risk=RiskLevel.MEDIUM,
                requires_approval=True,
            )
        ],
        risk=RiskLevel.MEDIUM,
        requires_approval=True,
    )


def test_same_plan_has_same_digest() -> None:
    first = make_plan(
        "INV-8231"
    )

    second = make_plan(
        "INV-8231"
    )

    assert (
        compute_plan_digest(first)
        == compute_plan_digest(second)
    )


def test_changed_plan_has_different_digest() -> None:
    first = make_plan(
        "INV-8231"
    )

    changed = make_plan(
        "INV-9999"
    )

    assert (
        compute_plan_digest(first)
        != compute_plan_digest(changed)
    )