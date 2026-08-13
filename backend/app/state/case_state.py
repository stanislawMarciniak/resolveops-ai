from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import Field

from app.models import (
    Approval,
    Evidence,
    ExecutedAction,
    Hypothesis,
    PlanReview,
    ResolutionPlan,
    VerificationResult,
)
from app.models.base import DomainModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class CaseStage(StrEnum):
    NEW = "NEW"
    INVESTIGATING = "INVESTIGATING"
    PLANNING = "PLANNING"
    REVIEW = "REVIEW"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"

    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    FAILED = "FAILED"


TERMINAL_CASE_STAGES = frozenset(
    {
        CaseStage.RESOLVED,
        CaseStage.ESCALATED,
        CaseStage.FAILED,
    }
)


class CaseState(DomainModel):
    """Canonical persistent state of a ResolveOps case."""

    case_id: UUID = Field(default_factory=uuid4)

    customer_id: str = Field(
        min_length=1,
        max_length=64,
    )

    description: str = Field(
        min_length=1,
        max_length=4_000,
    )

    stage: CaseStage = CaseStage.NEW

    evidence: list[Evidence] = Field(
        default_factory=list,
        max_length=100,
    )

    hypotheses: list[Hypothesis] = Field(
        default_factory=list,
        max_length=25,
    )

    root_cause: str | None = Field(
        default=None,
        max_length=4_000,
    )

    resolution_plan: ResolutionPlan | None = None

    review: PlanReview | None = None

    plan_revision_count: int = Field(
        default=0,
        ge=0,
    )

    approval: Approval | None = None

    executed_actions: list[ExecutedAction] = Field(
        default_factory=list,
        max_length=25,
    )

    verification: VerificationResult | None = None

    # LLM / workflow metrics
    model_calls: int = Field(default=0, ge=0)
    tool_calls: int = Field(default=0, ge=0)

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)

    estimated_cost_usd: float = Field(
        default=0.0,
        ge=0.0,
    )

    tool_input_tokens: int = Field(
        default=0,
        ge=0,
    )

    thinking_tokens: int = Field(
        default=0,
        ge=0,
    )

    llm_latency_ms: float = Field(
        default=0.0,
        ge=0.0,
    )

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @property
    def is_terminal(self) -> bool:
        return self.stage in TERMINAL_CASE_STAGES