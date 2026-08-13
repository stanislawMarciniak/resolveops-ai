import asyncio

from app.agents.investigation_workflow import (
    InvestigationWorkflow,
)
from app.config import get_settings
from app.state import (
    CaseState,
    CaseStateRepository,
    SessionLocal,
    init_db,
)

CASE_DESCRIPTION = """
ACME reports that its enterprise account is
suspended despite paying invoice INV-8231
yesterday.
""".strip()


async def run_investigation_case(
    *,
    customer_id: str,
    description: str,
) -> CaseState:
    settings = get_settings()

    init_db()

    repository = CaseStateRepository(
        SessionLocal
    )

    state = repository.save(
        CaseState(
            customer_id=customer_id,
            description=description,
        )
    )

    workflow = InvestigationWorkflow(
        settings=settings,
        repository=repository,
    )

    return await workflow.run(
        state.case_id
    )


async def main() -> None:
    result = await run_investigation_case(
        customer_id="ACME",
        description=CASE_DESCRIPTION,
    )

    print(
        f"Case: {result.case_id}"
    )

    print("\nStage:")
    print(result.stage)

    print("\nRoot cause:")
    print(result.root_cause)

    print("\nEvidence:")
    for evidence in result.evidence:
        print(
            evidence.model_dump_json(
                indent=2
            )
        )

    print("\nHypotheses:")
    for hypothesis in result.hypotheses:
        print(
            hypothesis.model_dump_json(
                indent=2
            )
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