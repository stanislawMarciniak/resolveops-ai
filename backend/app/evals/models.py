from enum import StrEnum

from pydantic import Field

from app.models.base import DomainModel
from app.state import CaseStage


class EvalVariant(StrEnum):
    MULTI_AGENT = "multi_agent"
    SINGLE_AGENT = "single_agent"
    NO_REVIEWER = "no_reviewer"


class EvalGroundTruth(DomainModel):
    expected_final_stage: CaseStage

    root_cause_keyword_groups: list[
        list[str]
    ] = Field(
        default_factory=list,
    )

    expected_actions: list[str] | None = None

    expected_customer_id: str | None = None

    expected_review_verdict: str | None = None

    expected_requires_approval: bool | None = None


class EvalCase(DomainModel):
    eval_id: str

    customer_id: str

    description: str

    tags: list[str] = Field(
        default_factory=list,
    )

    ground_truth: EvalGroundTruth


class EvalDataset(DomainModel):
    name: str
    version: str
    cases: list[EvalCase]


class EvalCaseResult(DomainModel):
    eval_id: str
    case_id: str

    # Primary metric: operational end-to-end success.
    # Root-cause wording is intentionally not a gate.
    passed: bool

    # Historical strict metric: operational success
    # plus exact root-cause keyword coverage when
    # root-cause scoring applies.
    strict_passed: bool

    expected_stage: str
    actual_stage: str
    stage_correct: bool

    root_cause_score: float | None = None
    root_cause_correct: bool | None = None

    expected_actions: list[str] | None = None
    tags: list[str] = Field(
        default_factory=list,
    )
    actual_actions: list[str]
    plan_correct: bool | None = None

    customer_id_correct: bool | None = None

    expected_requires_approval: bool | None = None
    actual_requires_approval: bool | None = None
    approval_correct: bool | None = None

    expected_review_verdict: str | None = None
    actual_review_verdict: str | None = None
    review_correct: bool | None = None

    model_calls: int
    tool_calls: int

    input_tokens: int
    tool_input_tokens: int
    output_tokens: int
    thinking_tokens: int

    total_tokens: int

    llm_latency_ms: float
    estimated_cost_usd: float

    plan_revision_count: int
    run_error: str | None = None


class EvalSummary(DomainModel):
    variant: EvalVariant = EvalVariant.MULTI_AGENT
    scoring_version: str = "2.0-operational-primary"

    dataset_name: str
    dataset_version: str

    total_cases: int

    # Primary operational metric.
    passed_cases: int
    pass_rate: float

    # Secondary strict metric kept for transparency
    # and backwards comparison with the old scorer.
    strict_passed_cases: int
    strict_pass_rate: float

    stage_accuracy: float
    root_cause_accuracy: float | None
    average_root_cause_score: float | None
    plan_accuracy: float | None
    review_accuracy: float | None
    customer_id_accuracy: float | None
    approval_accuracy: float | None

    average_model_calls: float
    average_tool_calls: float
    average_tokens: float

    average_llm_latency_ms: float
    p50_llm_latency_ms: float
    p95_llm_latency_ms: float

    average_cost_usd: float
    total_cost_usd: float

    average_plan_revisions: float
    error_cases: int

    # Primary operational success by tag.
    tag_pass_rates: dict[str, float] = Field(
        default_factory=dict,
    )

    # Strict success by tag, retained separately.
    tag_strict_pass_rates: dict[str, float] = Field(
        default_factory=dict,
    )


class EvalReport(DomainModel):
    summary: EvalSummary
    cases: list[EvalCaseResult]
