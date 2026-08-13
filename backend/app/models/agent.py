from datetime import datetime

from pydantic import Field

from .base import DomainModel
from .enums import (
    ApprovalDecision,
    EvidenceSource,
    ExecutionStatus,
    ReviewVerdict,
    RiskLevel,
)

ScalarValue = str | int | float | bool | None


class Evidence(DomainModel):
    evidence_id: str = Field(min_length=1, max_length=64)

    source: EvidenceSource

    description: str = Field(min_length=1)

    details: dict[str, ScalarValue] = Field(
        default_factory=dict,
    )


class Hypothesis(DomainModel):
    hypothesis_id: str = Field(min_length=1, max_length=64)

    description: str = Field(min_length=1)

    evidence_ids: list[str] = Field(
        default_factory=list,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class PlannedAction(DomainModel):
    tool_name: str = Field(
        min_length=1,
        max_length=100,
    )

    arguments: dict[str, ScalarValue]

    reason: str = Field(
        min_length=1,
    )

    evidence_ids: list[str] = Field(
        default_factory=list,
    )

    risk: RiskLevel

    requires_approval: bool


class ResolutionPlan(DomainModel):
    explanation: str = Field(min_length=1)

    actions: list[PlannedAction] = Field(
        min_length=1,
    )

    risk: RiskLevel

    requires_approval: bool


class Approval(DomainModel):
    approval_id: str = Field(min_length=1, max_length=64)

    user_id: str | None = None

    decision: ApprovalDecision = ApprovalDecision.PENDING

    created_at: datetime

    decided_at: datetime | None = None

    plan_digest: str = Field(
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
    )


class ExecutedAction(DomainModel):
    tool_name: str = Field(min_length=1, max_length=100)

    arguments: dict[str, ScalarValue]

    status: ExecutionStatus

    started_at: datetime

    completed_at: datetime | None = None

    result_summary: str | None = None

    error: str | None = None


class VerificationCheck(DomainModel):
    name: str = Field(min_length=1)

    expected: str
    actual: str

    passed: bool


class VerificationResult(DomainModel):
    success: bool

    checks: list[VerificationCheck] = Field(
        default_factory=list,
    )

    summary: str = Field(min_length=1)

class PlanReview(DomainModel):
    verdict: ReviewVerdict

    summary: str = Field(
        min_length=1,
        max_length=2_000,
    )

    issues: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    revision_feedback: str | None = Field(
        default=None,
        max_length=2_000,
    )