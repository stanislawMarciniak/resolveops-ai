import pytest
from app.agents.planner import (
    PlannedActionOutput,
    PlannerResult,
    PlannerToolName,
    to_resolution_plan,
)
from app.models import RiskLevel
from pydantic import ValidationError


def test_match_payment_requires_ids() -> None:
    with pytest.raises(
        ValidationError
    ):
        PlannedActionOutput(
            tool_name=(
                PlannerToolName
                .MATCH_PAYMENT
            ),
            reason="Match payment.",
        )


def test_planner_result_becomes_domain_plan() -> None:
    result = PlannerResult(
        explanation=(
            "Match the confirmed payment and "
            "then remove the billing hold."
        ),
        actions=[
            PlannedActionOutput(
                tool_name=(
                    PlannerToolName
                    .MATCH_PAYMENT
                ),
                payment_id="TX-9912",
                invoice_id="INV-8231",
                reason=(
                    "Payment is confirmed "
                    "but unmatched."
                ),
                evidence_ids=[
                    "E3",
                    "E4",
                ],
            ),
            PlannedActionOutput(
                tool_name=(
                    PlannerToolName
                    .REMOVE_ACCOUNT_HOLD
                ),
                reason=(
                    "Remove the billing hold "
                    "after payment matching."
                ),
                evidence_ids=[
                    "E1",
                    "E2",
                    "E5",
                ],
            ),
        ],
    )

    plan = to_resolution_plan(
        result,
        customer_id="ACME",
    )
    assert len(plan.actions) == 2

    match = plan.actions[0]

    assert (
        match.tool_name
        == "match_payment"
    )

    assert match.arguments == {
        "customer_id": "ACME",
        "payment_id": "TX-9912",
        "invoice_id": "INV-8231",
    }

    assert (
        match.risk
        is RiskLevel.MEDIUM
    )

    assert match.requires_approval

    assert plan.requires_approval

    assert (
        plan.risk
        is RiskLevel.MEDIUM
    )