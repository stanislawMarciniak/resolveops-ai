from app.evals.models import (
    EvalCaseResult,
    EvalReport,
    EvalSummary,
    EvalVariant,
)


def _average(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    return sum(values) / len(
        values
    )


def _optional_average(
    values: list[float | None],
) -> float | None:
    applicable = [
        value
        for value in values
        if value is not None
    ]

    if not applicable:
        return None

    return _average(
        applicable
    )


def _optional_accuracy(
    values: list[bool | None],
) -> float | None:
    applicable = [
        value
        for value in values
        if value is not None
    ]

    if not applicable:
        return None

    return (
        sum(
            1
            for value in applicable
            if value
        )
        / len(applicable)
    )


def _percentile(
    values: list[float],
    percentile: float,
) -> float:
    if not values:
        return 0.0

    ordered = sorted(
        values
    )

    if len(ordered) == 1:
        return ordered[0]

    position = (
        percentile
        * (len(ordered) - 1)
    )

    lower_index = int(
        position
    )

    upper_index = min(
        lower_index + 1,
        len(ordered) - 1,
    )

    fraction = (
        position
        - lower_index
    )

    return (
        ordered[lower_index]
        * (1.0 - fraction)
        + ordered[upper_index]
        * fraction
    )


def _tag_rates(
    *,
    results: list[EvalCaseResult],
    strict: bool,
) -> dict[str, float]:
    all_tags = sorted(
        {
            tag
            for result in results
            for tag in result.tags
        }
    )

    rates: dict[str, float] = {}

    for tag in all_tags:
        tagged_results = [
            result
            for result in results
            if tag in result.tags
        ]

        rates[tag] = (
            sum(
                1
                for result in tagged_results
                if (
                    result.strict_passed
                    if strict
                    else result.passed
                )
            )
            / len(tagged_results)
        )

    return rates


def build_report(
    *,
    variant: EvalVariant,
    dataset_name: str,
    dataset_version: str,
    results: list[EvalCaseResult],
) -> EvalReport:
    total_cases = len(
        results
    )

    passed_cases = sum(
        1
        for result in results
        if result.passed
    )

    strict_passed_cases = sum(
        1
        for result in results
        if result.strict_passed
    )

    stage_accuracy = (
        0.0
        if total_cases == 0
        else (
            sum(
                1
                for result in results
                if result.stage_correct
            )
            / total_cases
        )
    )

    latencies = [
        result.llm_latency_ms
        for result in results
    ]

    costs = [
        result.estimated_cost_usd
        for result in results
    ]

    summary = EvalSummary(
        variant=variant,
        dataset_name=dataset_name,
        dataset_version=(
            dataset_version
        ),
        total_cases=total_cases,
        passed_cases=passed_cases,
        pass_rate=(
            0.0
            if total_cases == 0
            else (
                passed_cases
                / total_cases
            )
        ),
        strict_passed_cases=(
            strict_passed_cases
        ),
        strict_pass_rate=(
            0.0
            if total_cases == 0
            else (
                strict_passed_cases
                / total_cases
            )
        ),
        stage_accuracy=stage_accuracy,
        root_cause_accuracy=(
            _optional_accuracy(
                [
                    result.root_cause_correct
                    for result in results
                ]
            )
        ),
        average_root_cause_score=(
            _optional_average(
                [
                    result.root_cause_score
                    for result in results
                ]
            )
        ),
        plan_accuracy=(
            _optional_accuracy(
                [
                    result.plan_correct
                    for result in results
                ]
            )
        ),
        review_accuracy=(
            _optional_accuracy(
                [
                    result.review_correct
                    for result in results
                ]
            )
        ),
        customer_id_accuracy=(
            _optional_accuracy(
                [
                    result.customer_id_correct
                    for result in results
                ]
            )
        ),
        approval_accuracy=(
            _optional_accuracy(
                [
                    result.approval_correct
                    for result in results
                ]
            )
        ),
        average_model_calls=(
            _average(
                [
                    float(
                        result.model_calls
                    )
                    for result in results
                ]
            )
        ),
        average_tool_calls=(
            _average(
                [
                    float(
                        result.tool_calls
                    )
                    for result in results
                ]
            )
        ),
        average_tokens=(
            _average(
                [
                    float(
                        result.total_tokens
                    )
                    for result in results
                ]
            )
        ),
        average_llm_latency_ms=(
            _average(latencies)
        ),
        p50_llm_latency_ms=(
            _percentile(
                latencies,
                0.50,
            )
        ),
        p95_llm_latency_ms=(
            _percentile(
                latencies,
                0.95,
            )
        ),
        average_cost_usd=(
            _average(costs)
        ),
        total_cost_usd=sum(
            costs
        ),
        tag_pass_rates=(
            _tag_rates(
                results=results,
                strict=False,
            )
        ),
        tag_strict_pass_rates=(
            _tag_rates(
                results=results,
                strict=True,
            )
        ),
        average_plan_revisions=(
            _average(
                [
                    float(
                        result.plan_revision_count
                    )
                    for result in results
                ]
            )
        ),
        error_cases=sum(
            1
            for result in results
            if result.run_error is not None
        ),
    )

    return EvalReport(
        summary=summary,
        cases=results,
    )
