import asyncio
import logging

from app.agents.model_config import (
    configure_adk_environment,
)
from app.agents.runtime import (
    run_structured_agent,
)
from app.agents.smoke_agent import (
    CaseIntakeSummary,
    build_smoke_agent,
)
from app.config import get_settings

DEMO_CASE = """
Customer ACME reports that its enterprise
account is suspended despite paying invoice
INV-8231 yesterday.
""".strip()


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s "
            "%(levelname)s "
            "%(name)s "
            "%(message)s"
        ),
    )

    settings = get_settings()

    configure_adk_environment(
        settings
    )

    agent = build_smoke_agent(
        settings
    )

    result = await run_structured_agent(
        agent=agent,
        prompt=DEMO_CASE,
        output_type=CaseIntakeSummary,
        app_name=settings.adk_app_name,
        max_llm_calls=(
            settings.max_llm_calls_per_run
        ),
    )

    print("\nStructured output:")
    print(
        result.output.model_dump_json(
            indent=2
        )
    )

    print("\nMetrics:")
    print(
        result.metrics.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    asyncio.run(main())