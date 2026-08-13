import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.models import (
    Approval,
    ApprovalDecision,
    ResolutionPlan,
    ReviewVerdict,
)
from app.state import (
    CaseStage,
    CaseState,
    CaseStateRepository,
)


class ApprovalError(RuntimeError):
    """Raised when a human approval transition is invalid."""


def utc_now() -> datetime:
    return datetime.now(UTC)


def compute_plan_digest(
    plan: ResolutionPlan,
) -> str:
    payload = json.dumps(
        plan.model_dump(
            mode="json"
        ),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


def build_pending_approval(
    plan: ResolutionPlan,
) -> Approval:
    return Approval(
        approval_id=str(
            uuid4()
        ),
        decision=(
            ApprovalDecision.PENDING
        ),
        plan_digest=(
            compute_plan_digest(plan)
        ),
        created_at=utc_now(),
    )


class ApprovalService:
    def __init__(
        self,
        repository: CaseStateRepository,
    ) -> None:
        self._repository = repository

    def decide(
        self,
        *,
        case_id: UUID | str,
        user_id: str,
        decision: ApprovalDecision,
    ) -> CaseState:
        state = self._repository.require(
            case_id
        )

        if (
            state.stage
            is not CaseStage.AWAITING_APPROVAL
        ):
            raise ApprovalError(
                "Case is not awaiting approval."
            )

        if state.resolution_plan is None:
            raise ApprovalError(
                "Case does not have a "
                "resolution plan."
            )

        if (
            state.review is None
            or state.review.verdict
            is not ReviewVerdict.APPROVE
        ):
            raise ApprovalError(
                "Plan has not been approved "
                "by Reviewer."
            )

        approval = state.approval

        if approval is None:
            raise ApprovalError(
                "Case does not have a pending "
                "approval request."
            )

        expected_digest = (
            compute_plan_digest(
                state.resolution_plan
            )
        )

        if (
            approval.plan_digest
            != expected_digest
        ):
            raise ApprovalError(
                "Approval belongs to a "
                "different plan version."
            )

        if (
            approval.decision
            is not ApprovalDecision.PENDING
        ):
            if (
                approval.decision is decision
                and approval.user_id
                == user_id
            ):
                return state

            raise ApprovalError(
                "Approval has already "
                "been decided."
            )

        if (
            decision
            is ApprovalDecision.PENDING
        ):
            raise ApprovalError(
                "Human decision must be "
                "APPROVED or REJECTED."
            )

        decided = approval.model_copy(
            update={
                "decision": decision,
                "user_id": user_id,
                "decided_at": utc_now(),
            }
        )

        if (
            decision
            is ApprovalDecision.APPROVED
        ):
            next_stage = (
                CaseStage.EXECUTING
            )
        else:
            next_stage = (
                CaseStage.ESCALATED
            )

        return self._repository.save(
            state.model_copy(
                update={
                    "approval": decided,
                    "stage": next_stage,
                }
            )
        )