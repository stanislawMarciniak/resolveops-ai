import argparse
import asyncio
from uuid import UUID

from app.agents.planning_workflow import (
    PlanningReviewWorkflow,
)
from app.config import get_settings
from app.state import (
    CaseState,
    CaseStateRepository,
    SessionLocal,
    init_db,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run ResolveOps planning and "
            "review for an existing case."
        )
    )

    parser.add_argument(
        "case_id",
        help="Case UUID.",
    )

    return parser.parse_args()


async def run_planning_review_case(
    case_id: UUID | str,
) -> CaseState:
    settings = get_settings()

    init_db()

    repository = CaseStateRepository(
        SessionLocal
    )

    workflow = PlanningReviewWorkflow(
        settings=settings,
        repository=repository,
    )

    return await workflow.run(
        case_id
    )


async def main() -> None:
    args = parse_args()

    result = await run_planning_review_case(
        args.case_id
    )

    print("\nStage:")
    print(result.stage)

    print("\nPlan:")

    if result.resolution_plan is None:
        print("None")

    else:
        print(
            result
            .resolution_plan
            .model_dump_json(
                indent=2
            )
        )

    print("\nReview:")

    if result.review is None:
        print("None")

    else:
        print(
            result.review.model_dump_json(
                indent=2
            )
        )

    print("\nPlan revisions:")
    print(
        result.plan_revision_count
    )

    print("\nMetrics:")
    print(
        {
            "model_calls": (
                result.model_calls
            ),
            "tool_calls": (
                result.tool_calls
            ),
            "input_tokens": (
                result.input_tokens
            ),
            "output_tokens": (
                result.output_tokens
            ),
        }
    )


if __name__ == "__main__":
    asyncio.run(main())