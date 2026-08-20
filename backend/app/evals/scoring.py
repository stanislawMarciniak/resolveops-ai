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
    evaluate_review: bool = True,
) -> EvalCaseResult:
    truth = definition.ground_truth

    stage_correct = (
        state.stage
        is truth.expected_final_stage
    )

    # Root-cause wording is evaluated only for cases
    # expected to proceed toward remediation. For
    # intentional escalations, the operational choice
    # to stop automation is the primary target.
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

    customer_id_correct: bool | None = None

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

    actual_requires_approval = (
        None
        if state.resolution_plan is None
        else state.resolution_plan.requires_approval
    )

    approval_correct: bool | None = None

    if (
        truth.expected_requires_approval
        is not None
    ):
        approval_correct = (
            actual_requires_approval
            is truth.expected_requires_approval
        )

    actual_review_verdict = (
        None
        if state.review is None
        else state.review.verdict.value
    )

    review_correct: bool | None = None

    if (
        evaluate_review
        and truth.expected_review_verdict
        is not None
    ):
        review_correct = (
            actual_review_verdict
            == truth.expected_review_verdict
        )

    # Primary methodology: operational success.
    # The final stage, mutation plan, canonical tool
    # arguments and approval requirement determine
    # whether the system made the right operational
    # decision. Exact root-cause wording remains a
    # separate diagnosis-quality metric.
    operational_checks = [
        stage_correct,
    ]

    if plan_correct is not None:
        operational_checks.append(
            plan_correct
        )

    if customer_id_correct is not None:
        operational_checks.append(
            customer_id_correct
        )

    if approval_correct is not None:
        operational_checks.append(
            approval_correct
        )

    passed = all(
        operational_checks
    )

    # Strict metric preserves the previous behavior:
    # exact root-cause keyword coverage is an
    # additional binary gate when applicable.
    strict_checks = list(
        operational_checks
    )

    if root_correct is not None:
        strict_checks.append(
            root_correct
        )

    strict_passed = all(
        strict_checks
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
        passed=passed,
        strict_passed=strict_passed,
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
        expected_requires_approval=(
            truth.expected_requires_approval
        ),
        actual_requires_approval=(
            actual_requires_approval
        ),
        approval_correct=approval_correct,
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
    evaluate_review: bool = True,
) -> EvalCaseResult:
    truth = definition.ground_truth

    root_applicable = (
        truth.expected_final_stage
        is not CaseStage.ESCALATED
        and bool(
            truth.root_cause_keyword_groups
        )
    )

    return EvalCaseResult(
        eval_id=definition.eval_id,
        case_id="",
        passed=False,
        strict_passed=False,
        expected_stage=(
            truth.expected_final_stage.value
        ),
        actual_stage="ERROR",
        stage_correct=False,
        root_cause_score=(
            0.0
            if root_applicable
            else None
        ),
        root_cause_correct=(
            False
            if root_applicable
            else None
        ),
        expected_actions=(
            truth.expected_actions
        ),
        tags=definition.tags,
        actual_actions=[],
        plan_correct=(
            False
            if truth.expected_actions is not None
            else None
        ),
        customer_id_correct=(
            False
            if truth.expected_customer_id is not None
            else None
        ),
        expected_requires_approval=(
            truth.expected_requires_approval
        ),
        actual_requires_approval=None,
        approval_correct=(
            False
            if truth.expected_requires_approval
            is not None
            else None
        ),
        expected_review_verdict=(
            truth.expected_review_verdict
        ),
        actual_review_verdict=None,
        review_correct=(
            False
            if (
                evaluate_review
                and truth.expected_review_verdict
                is not None
            )
            else None
        ),
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
