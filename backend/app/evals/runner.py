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
)
from app.evals.report import (
    build_report,
)
from app.evals.scoring import (
    score_case,
    score_error_case,
)
from app.state import (
    CaseStage,
    CaseState,
)


DEFAULT_DATASET = Path(
    "data/evals/resolveops_eval_v1.json"
)

DEFAULT_OUTPUT = Path(
    "data/evals/results/"
    "multi_agent_v1.json"
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
) -> CaseState:
    state = (
        await run_investigation_case(
            customer_id=(
                definition.customer_id
            ),
            description=(
                definition.description
            ),
        )
    )

    if (
        state.stage
        is CaseStage.PLANNING
    ):
        state = (
            await run_planning_review_case(
                state.case_id
            )
        )

    return state


async def run_single_eval(
    *,
    index: int,
    total: int,
    definition: EvalCase,
    semaphore: asyncio.Semaphore,
) -> tuple[int, EvalCaseResult]:
    async with semaphore:
        print(
            f"[{index + 1}/{total}] "
            f"{definition.eval_id} START"
        )

        try:
            state = await run_eval_case(
                definition
            )

            result = score_case(
                definition=definition,
                state=state,
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
            )

        status = (
            "PASS"
            if result.passed
            else "FAIL"
        )

        print(
            f"[{index + 1}/{total}] "
            f"{definition.eval_id} "
            f"{status} "
            f"stage={result.actual_stage} "
            f"calls={result.model_calls} "
            f"cost=${result.estimated_cost_usd:.4f}"
        )

        return index, result


async def run_dataset(
    dataset: EvalDataset,
    *,
    limit: int | None = None,
    concurrency: int = 3,
) -> list[EvalCaseResult]:
    definitions = dataset.cases

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


async def async_main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    parser.add_argument(
        "--limit",
        type=int,
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
        limit=args.limit,
        concurrency=args.concurrency,
    )

    report = build_report(
        dataset_name=dataset.name,
        dataset_version=(
            dataset.version
        ),
        results=results,
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
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
        f"Saved: {args.output}"
    )


def main() -> None:
    asyncio.run(
        async_main()
    )


if __name__ == "__main__":
    main()