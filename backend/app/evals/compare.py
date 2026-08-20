import json
from pathlib import Path
from typing import Any

from app.evals.models import (
    EvalCaseResult,
    EvalReport,
    EvalVariant,
)

RESULTS_DIR = Path(
    "data/evals/results"
)

MULTI_AGENT_PATH = (
    RESULTS_DIR
    / "multi_agent.json"
)

MULTI_AGENT_FALLBACK_PATH = (
    RESULTS_DIR
    / "multi_agent_v1.json"
)

SINGLE_AGENT_PATH = (
    RESULTS_DIR
    / "single_agent.json"
)

NO_REVIEWER_PATH = (
    RESULTS_DIR
    / "no_reviewer.json"
)

OUTPUT_PATH = (
    RESULTS_DIR
    / "final_comparison.json"
)


def _load_report(
    path: Path,
) -> EvalReport:
    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    summary = payload.get(
        "summary",
        {},
    )

    # Prevent accidentally mixing the old strict-only
    # scorer with the new operational-primary scorer.
    if (
        summary.get("scoring_version")
        != "2.0-operational-primary"
    ):
        raise ValueError(
            f"{path} was generated with an old "
            "evaluation methodology. Re-run this "
            "variant before comparing results."
        )

    return EvalReport.model_validate(
        payload
    )


def _case_map(
    report: EvalReport,
) -> dict[str, EvalCaseResult]:
    return {
        result.eval_id: result
        for result in report.cases
    }


def _validate_reports(
    reports: list[EvalReport],
) -> None:
    if not reports:
        raise ValueError(
            "No reports supplied."
        )

    first = reports[0]

    for report in reports[1:]:
        if (
            report.summary.dataset_name
            != first.summary.dataset_name
            or report.summary.dataset_version
            != first.summary.dataset_version
        ):
            raise ValueError(
                "Evaluation reports use different "
                "datasets or dataset versions."
            )

        if (
            set(_case_map(report))
            != set(_case_map(first))
        ):
            raise ValueError(
                "Evaluation reports contain "
                "different case sets."
            )


def _summary_payload(
    report: EvalReport,
) -> dict[str, Any]:
    summary = report.summary

    return {
        "operational_pass_rate": (
            summary.pass_rate
        ),
        "strict_pass_rate": (
            summary.strict_pass_rate
        ),
        "stage_accuracy": (
            summary.stage_accuracy
        ),
        "root_cause_accuracy": (
            summary.root_cause_accuracy
        ),
        "average_root_cause_score": (
            summary.average_root_cause_score
        ),
        "plan_accuracy": (
            summary.plan_accuracy
        ),
        "review_accuracy": (
            summary.review_accuracy
        ),
        "customer_id_accuracy": (
            summary.customer_id_accuracy
        ),
        "approval_accuracy": (
            summary.approval_accuracy
        ),
        "average_model_calls": (
            summary.average_model_calls
        ),
        "average_tool_calls": (
            summary.average_tool_calls
        ),
        "average_tokens": (
            summary.average_tokens
        ),
        "average_llm_latency_ms": (
            summary.average_llm_latency_ms
        ),
        "p50_llm_latency_ms": (
            summary.p50_llm_latency_ms
        ),
        "p95_llm_latency_ms": (
            summary.p95_llm_latency_ms
        ),
        "average_cost_usd": (
            summary.average_cost_usd
        ),
        "total_cost_usd": (
            summary.total_cost_usd
        ),
        "error_cases": (
            summary.error_cases
        ),
        "tag_pass_rates": (
            summary.tag_pass_rates
        ),
        "tag_strict_pass_rates": (
            summary.tag_strict_pass_rates
        ),
    }


def _difference(
    left: float | None,
    right: float | None,
) -> float | None:
    if (
        left is None
        or right is None
    ):
        return None

    return left - right


def _ratio(
    numerator: float | None,
    denominator: float | None,
) -> float | None:
    if (
        numerator is None
        or denominator is None
        or denominator == 0.0
    ):
        return None

    return numerator / denominator


def _paired_comparison(
    *,
    left: EvalReport,
    right: EvalReport,
) -> dict[str, Any]:
    left_cases = _case_map(
        left
    )
    right_cases = _case_map(
        right
    )

    case_ids = sorted(
        left_cases
    )

    left_only_passes = [
        case_id
        for case_id in case_ids
        if (
            left_cases[case_id].passed
            and not right_cases[case_id].passed
        )
    ]

    right_only_passes = [
        case_id
        for case_id in case_ids
        if (
            right_cases[case_id].passed
            and not left_cases[case_id].passed
        )
    ]

    left_only_strict_passes = [
        case_id
        for case_id in case_ids
        if (
            left_cases[case_id].strict_passed
            and not right_cases[case_id].strict_passed
        )
    ]

    right_only_strict_passes = [
        case_id
        for case_id in case_ids
        if (
            right_cases[case_id].strict_passed
            and not left_cases[case_id].strict_passed
        )
    ]

    return {
        "operational_pass_rate_delta": (
            left.summary.pass_rate
            - right.summary.pass_rate
        ),
        "strict_pass_rate_delta": (
            left.summary.strict_pass_rate
            - right.summary.strict_pass_rate
        ),
        "stage_accuracy_delta": (
            left.summary.stage_accuracy
            - right.summary.stage_accuracy
        ),
        "root_cause_accuracy_delta": (
            _difference(
                left.summary.root_cause_accuracy,
                right.summary.root_cause_accuracy,
            )
        ),
        "root_cause_accuracy_ratio": (
            _ratio(
                left.summary.root_cause_accuracy,
                right.summary.root_cause_accuracy,
            )
        ),
        "average_root_cause_score_delta": (
            _difference(
                left.summary.average_root_cause_score,
                right.summary.average_root_cause_score,
            )
        ),
        "average_cost_delta_usd": (
            left.summary.average_cost_usd
            - right.summary.average_cost_usd
        ),
        "average_model_calls_delta": (
            left.summary.average_model_calls
            - right.summary.average_model_calls
        ),
        "average_latency_delta_ms": (
            left.summary.average_llm_latency_ms
            - right.summary.average_llm_latency_ms
        ),
        "left_only_operational_passes": (
            left_only_passes
        ),
        "right_only_operational_passes": (
            right_only_passes
        ),
        "left_only_strict_passes": (
            left_only_strict_passes
        ),
        "right_only_strict_passes": (
            right_only_strict_passes
        ),
    }


def _tag_comparison(
    reports: dict[EvalVariant, EvalReport],
    *,
    strict: bool,
) -> dict[str, dict[str, float | None]]:
    all_tags = sorted(
        {
            tag
            for report in reports.values()
            for tag in (
                report.summary.tag_strict_pass_rates
                if strict
                else report.summary.tag_pass_rates
            )
        }
    )

    comparison: dict[
        str,
        dict[str, float | None],
    ] = {}

    for tag in all_tags:
        comparison[tag] = {}

        for variant, report in reports.items():
            rates = (
                report.summary.tag_strict_pass_rates
                if strict
                else report.summary.tag_pass_rates
            )

            comparison[tag][variant.value] = (
                rates.get(tag)
            )

    return comparison


def build_comparison(
    *,
    multi_agent: EvalReport,
    single_agent: EvalReport,
    no_reviewer: EvalReport,
) -> dict[str, Any]:
    _validate_reports(
        [
            multi_agent,
            single_agent,
            no_reviewer,
        ]
    )

    reports = {
        EvalVariant.MULTI_AGENT: multi_agent,
        EvalVariant.SINGLE_AGENT: single_agent,
        EvalVariant.NO_REVIEWER: no_reviewer,
    }

    multi_vs_single = _paired_comparison(
        left=multi_agent,
        right=single_agent,
    )

    reviewer_comparison = _paired_comparison(
        left=multi_agent,
        right=no_reviewer,
    )

    multi_cases = _case_map(
        multi_agent
    )
    no_reviewer_cases = _case_map(
        no_reviewer
    )

    case_ids = sorted(
        multi_cases
    )

    reviewer_saved_cases = [
        case_id
        for case_id in case_ids
        if (
            multi_cases[case_id].passed
            and not no_reviewer_cases[case_id].passed
        )
    ]

    reviewer_hurt_cases = [
        case_id
        for case_id in case_ids
        if (
            no_reviewer_cases[case_id].passed
            and not multi_cases[case_id].passed
        )
    ]

    return {
        "dataset": {
            "name": (
                multi_agent.summary.dataset_name
            ),
            "version": (
                multi_agent.summary.dataset_version
            ),
            "cases": (
                multi_agent.summary.total_cases
            ),
        },
        "methodology": {
            "scoring_version": (
                "2.0-operational-primary"
            ),
            "primary_metric": (
                "operational end-to-end success"
            ),
            "primary_pass_definition": (
                "correct final stage plus exact "
                "expected mutation plan, canonical "
                "customer ID and approval requirement "
                "when those fields apply; exact root-"
                "cause wording is reported separately"
            ),
            "strict_metric": (
                "operational success plus exact root-"
                "cause keyword coverage when applicable"
            ),
            "dataset_usage": (
                "development/internal evaluation suite; "
                "results are not claimed as unseen "
                "holdout performance"
            ),
            "reviewer_ablation_caveat": (
                "Reviewer and no-Reviewer variants are "
                "independent stochastic runs, so the "
                "difference is not a perfectly isolated "
                "causal estimate of Reviewer effect."
            ),
        },
        "variants": {
            variant.value: _summary_payload(
                report
            )
            for variant, report
            in reports.items()
        },
        "multi_vs_single": {
            **multi_vs_single,
            "multi_agent_only_passes": (
                multi_vs_single[
                    "left_only_operational_passes"
                ]
            ),
            "single_agent_only_passes": (
                multi_vs_single[
                    "right_only_operational_passes"
                ]
            ),
        },
        "reviewer_ablation": {
            **reviewer_comparison,
            "reviewer_saved_cases": (
                reviewer_saved_cases
            ),
            "reviewer_hurt_cases": (
                reviewer_hurt_cases
            ),
        },
        "tag_comparison": (
            _tag_comparison(
                reports,
                strict=False,
            )
        ),
        "tag_strict_comparison": (
            _tag_comparison(
                reports,
                strict=True,
            )
        ),
    }


def main() -> None:
    multi_agent = _load_report(
        MULTI_AGENT_PATH
    )

    single_agent = _load_report(
        SINGLE_AGENT_PATH
    )

    no_reviewer = _load_report(
        NO_REVIEWER_PATH
    )

    comparison = build_comparison(
        multi_agent=multi_agent,
        single_agent=single_agent,
        no_reviewer=no_reviewer,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            comparison,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"Saved: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
