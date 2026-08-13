import re

from app.evals.models import (
    EvalCase,
    EvalCaseResult,
)
from app.state import (
    CaseStage,
    CaseState,
)


def _normalize(
    value: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        value.casefold(),
    ).strip()


def root_cause_score(
    *,
    root_cause: str | None,
    keyword_groups: list[list[str]],
) -> float | None:
    if not keyword_groups:
        return None

    if root_cause is None:
        return 0.0

    normalized = _normalize(
        root_cause
    )

    matched = 0

    for group in keyword_groups:
        if any(
            _normalize(keyword)
            in normalized
            for keyword in group
        ):
            matched += 1

    return matched / len(
        keyword_groups
    )


def score_case(
    *,
    definition: EvalCase,
    state: CaseState,
) -> EvalCaseResult:
    truth = definition.ground_truth

    stage_correct = (
        state.stage
        is truth.expected_final_stage
    )

    if (
        truth.expected_final_stage
        is CaseStage.ESCALATED
    ):
        root_score = None
        root_correct = None

    else:
        root_score = root_cause_score(
            root_cause=state.root_cause,
            keyword_groups=(
                truth.root_cause_keyword_groups
            ),
        )

        root_correct = (
            None
            if root_score is None
            else root_score == 1.0
        )

    actual_actions = (
        []
        if state.resolution_plan is None
        else [
            action.tool_name
            for action
            in state.resolution_plan.actions
        ]
    )

    plan_correct: bool | None

    if truth.expected_actions is None:
        plan_correct = None
    else:
        plan_correct = (
            actual_actions
            == truth.expected_actions
        )

    customer_id_correct: (
        bool | None
    ) = None

    if (
        truth.expected_customer_id
        is not None
    ):
        if state.resolution_plan is None:
            customer_id_correct = False
        else:
            customer_id_correct = all(
                action.arguments.get(
                    "customer_id"
                )
                == truth.expected_customer_id
                for action
                in state.resolution_plan.actions
            )

    actual_review_verdict = (
        None
        if state.review is None
        else state.review.verdict.value
    )

    review_correct: bool | None = None

    if (
        truth.expected_review_verdict
        is not None
    ):
        review_correct = (
            actual_review_verdict
            == truth.expected_review_verdict
        )

    approval_correct = True

    if (
        truth.expected_requires_approval
        is not None
    ):
        approval_correct = (
            state.resolution_plan
            is not None
            and (
                state.resolution_plan
                .requires_approval
                is truth
                .expected_requires_approval
            )
        )

    required_checks = [
        stage_correct,
        approval_correct,
    ]

    if plan_correct is not None:
        required_checks.append(
            plan_correct
        )

    if root_correct is not None:
        required_checks.append(
            root_correct
        )

    if customer_id_correct is not None:
        required_checks.append(
            customer_id_correct
        )


    total_tokens = (
        state.input_tokens
        + state.tool_input_tokens
        + state.output_tokens
        + state.thinking_tokens
    )

    return EvalCaseResult(
        eval_id=definition.eval_id,
        case_id=str(
            state.case_id
        ),
        passed=all(
            required_checks
        ),
        expected_stage=(
            truth.expected_final_stage.value
        ),
        actual_stage=state.stage.value,
        stage_correct=stage_correct,
        root_cause_score=root_score,
        root_cause_correct=root_correct,
        expected_actions=(
            truth.expected_actions
        ),
        actual_actions=actual_actions,
        plan_correct=plan_correct,
        customer_id_correct=(
            customer_id_correct
        ),
        expected_review_verdict=(
            truth.expected_review_verdict
        ),
        actual_review_verdict=(
            actual_review_verdict
        ),
        review_correct=review_correct,
        model_calls=state.model_calls,
        tool_calls=state.tool_calls,
        input_tokens=state.input_tokens,
        tool_input_tokens=(
            state.tool_input_tokens
        ),
        output_tokens=state.output_tokens,
        thinking_tokens=(
            state.thinking_tokens
        ),
        total_tokens=total_tokens,
        llm_latency_ms=(
            state.llm_latency_ms
        ),
        estimated_cost_usd=(
            state.estimated_cost_usd
        ),
        plan_revision_count=(
            state.plan_revision_count
        ),
        tags=definition.tags,
    )

def score_error_case(
    *,
    definition: EvalCase,
    error: Exception,
) -> EvalCaseResult:
    truth = definition.ground_truth

    return EvalCaseResult(
        eval_id=definition.eval_id,
        case_id="",
        passed=False,
        expected_stage=(
            truth.expected_final_stage.value
        ),
        actual_stage="ERROR",
        stage_correct=False,
        root_cause_score=None,
        root_cause_correct=None,
        expected_actions=(
            truth.expected_actions
        ),
        tags=definition.tags,
        actual_actions=[],
        plan_correct=False,
        customer_id_correct=None,
        expected_review_verdict=(
            truth.expected_review_verdict
        ),
        actual_review_verdict=None,
        review_correct=None,
        model_calls=0,
        tool_calls=0,
        input_tokens=0,
        tool_input_tokens=0,
        output_tokens=0,
        thinking_tokens=0,
        total_tokens=0,
        llm_latency_ms=0.0,
        estimated_cost_usd=0.0,
        plan_revision_count=0,
        run_error=(
            f"{type(error).__name__}: "
            f"{error}"
        ),
    )