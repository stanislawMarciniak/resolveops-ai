from app.agents.runtime import (
    run_structured_agent,
)
from app.config import get_settings
from app.evals.single_agent import (
    SingleAgentOutcome,
    SingleAgentResult,
    build_single_agent,
    single_agent_plan,
)
from app.state import (
    CaseStage,
    CaseState,
    CaseStateRepository,
    SessionLocal,
)


async def run_single_agent_case(
    *,
    customer_id: str,
    description: str,
) -> CaseState:
    settings = get_settings()

    repository = CaseStateRepository(
        SessionLocal
    )

    state = CaseState(
        customer_id=customer_id,
        description=description,
        stage=CaseStage.INVESTIGATING,
    )

    state = repository.save(
        state
    )

    agent = build_single_agent(
        settings
    )

    prompt = (
        "Investigate and resolve this case.\n\n"
        f"Canonical customer ID: {customer_id}\n\n"
        f"Case description:\n{description}"
    )

    result = await run_structured_agent(
        agent=agent,
        prompt=prompt,
        output_type=SingleAgentResult,
        max_llm_calls=(
            settings
            .investigator_max_llm_calls
        ),
    )

    output = result.output

    plan = single_agent_plan(
        result=output,
        customer_id=customer_id,
    )

    if (
        output.outcome
        is SingleAgentOutcome.PROPOSE_PLAN
        and plan is not None
    ):
        stage = (
            CaseStage.AWAITING_APPROVAL
            if plan.requires_approval
            else CaseStage.EXECUTING
        )
    else:
        stage = CaseStage.ESCALATED

    raw_tool_calls = result.state.get(
        "investigator_tool_calls",
        0,
    )

    tool_calls = (
        raw_tool_calls
        if isinstance(
            raw_tool_calls,
            int,
        )
        else 0
    )

    metrics = result.metrics

    return repository.save(
        state.model_copy(
            update={
                "root_cause": (
                    output.root_cause
                ),
                "resolution_plan": plan,
                "stage": stage,
                "model_calls": (
                    metrics.model_calls
                ),
                "tool_calls": tool_calls,
                "input_tokens": (
                    metrics.input_tokens
                ),
                "tool_input_tokens": (
                    metrics
                    .tool_input_tokens
                ),
                "output_tokens": (
                    metrics.output_tokens
                ),
                "thinking_tokens": (
                    metrics
                    .thinking_tokens
                ),
                "llm_latency_ms": (
                    metrics
                    .model_latency_ms
                ),
                "estimated_cost_usd": (
                    metrics
                    .estimated_cost_usd
                ),
            }
        )
    )