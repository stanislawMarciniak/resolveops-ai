import argparse
import asyncio
import json
from pathlib import Path

from app.agents.run_investigation import (
    run_investigation_case,
)
from app.agents.run_planning_review import (
    run_planning_review_case,
)
from app.evals.models import (
    EvalCase,
    EvalCaseResult,
    EvalDataset,
    EvalVariant,
)
from app.evals.report import (
    build_report,
)
from app.evals.scoring import (
    score_case,
    score_error_case,
)
from app.evals.single_agent import (
    run_single_agent_case,
)
from app.state import (
    CaseStage,
    CaseState,
)

DEFAULT_DATASET = Path(
    "data/evals/resolveops_eval_v1.json"
)

RESULTS_DIR = Path(
    "data/evals/results"
)


def load_dataset(
    path: Path,
) -> EvalDataset:
    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    return EvalDataset.model_validate(
        payload
    )


async def run_eval_case(
    definition: EvalCase,
    *,
    variant: EvalVariant,
) -> CaseState:
    if variant is EvalVariant.SINGLE_AGENT:
        return await run_single_agent_case(
            customer_id=(
                definition.customer_id
            ),
            description=(
                definition.description
            ),
        )

    state = await run_investigation_case(
        customer_id=(
            definition.customer_id
        ),
        description=(
            definition.description
        ),
    )

    if state.stage is not CaseStage.PLANNING:
        return state

    return await run_planning_review_case(
        state.case_id,
        review_enabled=(
            variant
            is EvalVariant.MULTI_AGENT
        ),
    )


async def run_single_eval(
    *,
    index: int,
    total: int,
    definition: EvalCase,
    variant: EvalVariant,
    semaphore: asyncio.Semaphore,
) -> tuple[int, EvalCaseResult]:
    async with semaphore:
        print(
            f"[{index + 1}/{total}] "
            f"{definition.eval_id} START"
        )

        evaluate_review = (
            variant
            is EvalVariant.MULTI_AGENT
        )

        try:
            state = await run_eval_case(
                definition,
                variant=variant,
            )

            result = score_case(
                definition=definition,
                state=state,
                evaluate_review=(
                    evaluate_review
                ),
            )

        except Exception as exc:
            print(
                f"[{index + 1}/{total}] "
                f"{definition.eval_id} "
                f"ERROR: {exc}"
            )

            result = score_error_case(
                definition=definition,
                error=exc,
                evaluate_review=(
                    evaluate_review
                ),
            )

        status = (
            "PASS"
            if result.passed
            else "FAIL"
        )

        strict_status = (
            "PASS"
            if result.strict_passed
            else "FAIL"
        )

        print(
            f"[{index + 1}/{total}] "
            f"{definition.eval_id} "
            f"{status} "
            f"strict={strict_status} "
            f"stage={result.actual_stage} "
            f"calls={result.model_calls} "
            f"cost=${result.estimated_cost_usd:.4f}"
        )

        return index, result


async def run_dataset(
    dataset: EvalDataset,
    *,
    variant: EvalVariant,
    limit: int | None = None,
    concurrency: int = 3,
    eval_case: str | None = None,
) -> list[EvalCaseResult]:
    definitions = dataset.cases

    if eval_case is not None:
        definitions = [
            definition
            for definition in definitions
            if definition.eval_id == eval_case
        ]

        if not definitions:
            raise ValueError(
                "Unknown eval case: "
                f"{eval_case}"
            )

    if limit is not None:
        definitions = definitions[
            :limit
        ]

    if concurrency < 1:
        raise ValueError(
            "concurrency must be at least 1"
        )

    total = len(
        definitions
    )

    semaphore = asyncio.Semaphore(
        concurrency
    )

    tasks = [
        run_single_eval(
            index=index,
            total=total,
            definition=definition,
            variant=variant,
            semaphore=semaphore,
        )
        for index, definition
        in enumerate(definitions)
    ]

    completed = await asyncio.gather(
        *tasks
    )

    completed.sort(
        key=lambda item: item[0]
    )

    return [
        result
        for _, result in completed
    ]


def default_output_path(
    *,
    variant: EvalVariant,
    limit: int | None,
    eval_case: str | None,
) -> Path:
    if eval_case is not None:
        return (
            RESULTS_DIR
            / "smoke"
            / f"{variant.value}_{eval_case}.json"
        )

    if limit is not None:
        return (
            RESULTS_DIR
            / "smoke"
            / (
                f"{variant.value}_"
                f"limit_{limit}.json"
            )
        )

    return (
        RESULTS_DIR
        / f"{variant.value}.json"
    )


async def async_main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
    )

    parser.add_argument(
        "--variant",
        type=EvalVariant,
        choices=list(EvalVariant),
        default=EvalVariant.MULTI_AGENT,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--case",
        dest="eval_case",
        type=str,
        default=None,
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help=(
            "Maximum number of eval cases "
            "running concurrently."
        ),
    )

    args = parser.parse_args()

    dataset = load_dataset(
        args.dataset
    )

    results = await run_dataset(
        dataset,
        variant=args.variant,
        limit=args.limit,
        concurrency=args.concurrency,
        eval_case=args.eval_case,
    )

    report = build_report(
        variant=args.variant,
        dataset_name=dataset.name,
        dataset_version=(
            dataset.version
        ),
        results=results,
    )

    output = (
        args.output
        if args.output is not None
        else default_output_path(
            variant=args.variant,
            limit=args.limit,
            eval_case=args.eval_case,
        )
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        report.model_dump_json(
            indent=2
        ),
        encoding="utf-8",
    )

    print()
    print("=== Evaluation summary ===")

    print(
        report.summary.model_dump_json(
            indent=2
        )
    )

    print()

    print(
        f"Saved: {output}"
    )


def main() -> None:
    asyncio.run(
        async_main()
    )


if __name__ == "__main__":
    main()
