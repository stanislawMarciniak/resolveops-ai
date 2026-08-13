from app.agents.planning_workflow import (
    determine_review_transition,
)
from app.models import ReviewVerdict
from app.state import CaseStage


def test_approved_plan_waits_for_approval() -> None:
    stage, revisions = (
        determine_review_transition(
            verdict=(
                ReviewVerdict.APPROVE
            ),
            requires_approval=True,
            revision_count=0,
            max_revisions=1,
        )
    )

    assert (
        stage
        is CaseStage.AWAITING_APPROVAL
    )

    assert revisions == 0


def test_approved_safe_plan_can_execute() -> None:
    stage, _ = (
        determine_review_transition(
            verdict=(
                ReviewVerdict.APPROVE
            ),
            requires_approval=False,
            revision_count=0,
            max_revisions=1,
        )
    )

    assert (
        stage
        is CaseStage.EXECUTING
    )


def test_first_revision_returns_to_planner() -> None:
    stage, revisions = (
        determine_review_transition(
            verdict=(
                ReviewVerdict.REVISE
            ),
            requires_approval=True,
            revision_count=0,
            max_revisions=1,
        )
    )

    assert (
        stage
        is CaseStage.PLANNING
    )

    assert revisions == 1


def test_second_revision_escalates() -> None:
    stage, revisions = (
        determine_review_transition(
            verdict=(
                ReviewVerdict.REVISE
            ),
            requires_approval=True,
            revision_count=1,
            max_revisions=1,
        )
    )

    assert (
        stage
        is CaseStage.ESCALATED
    )

    assert revisions == 1


def test_reviewer_can_escalate_directly() -> None:
    stage, _ = (
        determine_review_transition(
            verdict=(
                ReviewVerdict.ESCALATE
            ),
            requires_approval=True,
            revision_count=0,
            max_revisions=1,
        )
    )

    assert (
        stage
        is CaseStage.ESCALATED
    )