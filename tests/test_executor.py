from datetime import UTC, datetime

import pytest
from app.approvals.service import (
    compute_plan_digest,
)
from app.execution.executor import (
    ExecutionError,
    validate_execution_authorization,
    validate_planned_action,
)
from app.models import (
    Approval,
    ApprovalDecision,
    Evidence,
    EvidenceSource,
    PlannedAction,
    PlanReview,
    ResolutionPlan,
    ReviewVerdict,
    RiskLevel,
)
from app.state import (
    CaseStage,
    CaseState,
)


def make_plan(
    customer_id: str = "ACME",
) -> ResolutionPlan:
    return ResolutionPlan(
        explanation="Fix payment matching.",
        actions=[
            PlannedAction(
                tool_name="match_payment",
                arguments={
                    "customer_id": customer_id,
                    "payment_id": "TX-9912",
                    "invoice_id": "INV-8231",
                },
                reason="Match payment.",
                evidence_ids=["E1"],
                risk=RiskLevel.MEDIUM,
                requires_approval=True,
            )
        ],
        risk=RiskLevel.MEDIUM,
        requires_approval=True,
    )


def make_state(
    *,
    customer_id: str = "ACME",
) -> CaseState:
    plan = make_plan(
        customer_id=customer_id
    )

    return CaseState(
        customer_id="ACME",
        description="Billing issue.",
        stage=CaseStage.EXECUTING,
        evidence=[
            Evidence(
                evidence_id="E1",
                source=EvidenceSource.BILLING,
                description="Payment exists.",
            )
        ],
        root_cause=(
            "Payment remained unmatched."
        ),
        resolution_plan=plan,
        review=PlanReview(
            verdict=ReviewVerdict.APPROVE,
            summary="Plan approved.",
        ),
        approval=Approval(
            approval_id="approval-1",
            user_id="operator@example.com",
            decision=(
                ApprovalDecision.APPROVED
            ),
            plan_digest=(
                compute_plan_digest(plan)
            ),
            created_at=(
                datetime.now(UTC)
            ),
            decided_at=(
                datetime.now(UTC)
            ),
        ),
    )


def test_valid_approval_allows_execution() -> None:
    state = make_state()

    plan = (
        validate_execution_authorization(
            state
        )
    )

    assert plan is state.resolution_plan


def test_modified_plan_invalidates_approval() -> None:
    state = make_state()

    changed_plan = make_plan(
        customer_id="GLOBEX"
    )

    changed = state.model_copy(
        update={
            "resolution_plan": (
                changed_plan
            )
        }
    )

    with pytest.raises(
        ExecutionError
    ):
        validate_execution_authorization(
            changed
        )


def test_wrong_customer_is_rejected() -> None:
    state = make_state(
        customer_id="000018392"
    )

    action = (
        state.resolution_plan.actions[0]  # type: ignore[union-attr]
    )

    with pytest.raises(
        ExecutionError
    ):
        validate_planned_action(
            state=state,
            action=action,
        )