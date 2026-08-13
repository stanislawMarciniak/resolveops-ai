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


async def run_dataset(
    dataset: EvalDataset,
    *,
    limit: int | None = None,
) -> list[EvalCaseResult]:
    definitions = dataset.cases

    if limit is not None:
        definitions = definitions[
            :limit
        ]

    results: list[
        EvalCaseResult
    ] = []

    total = len(
        definitions
    )

    for index, definition in enumerate(
        definitions,
        start=1,
    ):
        print(
            f"[{index}/{total}] "
            f"{definition.eval_id}"
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
                f"  ERROR: {exc}"
            )

            continue

        results.append(
            result
        )

        status = (
            "PASS"
            if result.passed
            else "FAIL"
        )

        print(
            f"  {status} "
            f"stage={result.actual_stage} "
            f"calls={result.model_calls} "
            f"cost=${result.estimated_cost_usd:.4f}"
        )

    return results


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

    args = parser.parse_args()

    dataset = load_dataset(
        args.dataset
    )

    results = await run_dataset(
        dataset,
        limit=args.limit,
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