from dataclasses import dataclass
from time import perf_counter
from typing import Any
from uuid import uuid4

from google.adk.agents import LlmAgent
from google.adk.agents.run_config import (
    RunConfig,
)
from google.adk.runners import Runner
from google.adk.sessions import (
    InMemorySessionService,
)
from google.genai import types
from opentelemetry import trace
from pydantic import (
    BaseModel,
    ValidationError,
)

from app.agents.callbacks import (
    MODEL_LATENCY_MS_KEY,
)
from app.agents.metrics import (
    AgentRunMetrics,
    UsageAccumulator,
)
from app.config import get_settings

tracer = trace.get_tracer(
    __name__
)


class AgentRuntimeError(RuntimeError):
    """Raised when an ADK agent run cannot produce valid output."""


@dataclass(frozen=True)
class AgentSessionResult:
    final_text: str | None

    state: dict[str, Any]

    metrics: AgentRunMetrics


@dataclass(frozen=True)
class StructuredAgentResult[TOutput: BaseModel]:
    output: TOutput

    metrics: AgentRunMetrics


async def run_agent_with_state(
    *,
    agent: LlmAgent,
    prompt: str,
    app_name: str,
    max_llm_calls: int,
    initial_state: (
        dict[str, Any] | None
    ) = None,
    user_id: str = "system",
) -> AgentSessionResult:
    settings = get_settings()

    session_service = (
        InMemorySessionService()  # type: ignore[no-untyped-call]
    )

    session_id = (
        f"{agent.name}-{uuid4()}"
    )

    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=initial_state or {},
    )

    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service,
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=prompt,
            )
        ],
    )

    run_config = RunConfig(
        max_llm_calls=max_llm_calls,
    )

    usage = UsageAccumulator()

    final_text: str | None = None

    started_at = perf_counter()

    with tracer.start_as_current_span(
        "resolveops.agent.run"
    ) as span:
        span.set_attribute(
            "resolveops.agent.name",
            agent.name,
        )

        span.set_attribute(
            "gen_ai.request.model",
            settings.adk_model,
        )

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
            run_config=run_config,
        ):
            if (
                event.usage_metadata
                is not None
            ):
                usage.add(
                    event.usage_metadata
                )

            if not event.is_final_response():
                continue

            if (
                event.content is None
                or not event.content.parts
            ):
                continue

            text_parts = [
                part.text
                for part in event.content.parts
                if part.text
            ]

            if text_parts:
                final_text = "".join(
                    text_parts
                )

        latency_ms = (
            perf_counter() - started_at
        ) * 1000.0

        session = (
            await session_service.get_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
            )
        )

        if session is None:
            raise AgentRuntimeError(
                "ADK session disappeared "
                "after agent execution."
            )

        raw_model_latency = (
            session.state.get(
                MODEL_LATENCY_MS_KEY,
                0.0,
            )
        )

        model_latency_ms = (
            float(raw_model_latency)
            if isinstance(
                raw_model_latency,
                int | float,
            )
            else 0.0
        )

        run_metrics = usage.build(
            latency_ms=latency_ms,
            model_latency_ms=(
                model_latency_ms
            ),
            input_cost_per_million=(
                settings
                .model_input_cost_per_million
            ),
            output_cost_per_million=(
                settings
                .model_output_cost_per_million
            ),
        )

        span.set_attribute(
            "resolveops.llm.model_calls",
            run_metrics.model_calls,
        )

        span.set_attribute(
            "resolveops.llm.input_tokens",
            run_metrics.input_tokens,
        )

        span.set_attribute(
            "resolveops.llm.output_tokens",
            run_metrics.output_tokens,
        )

        span.set_attribute(
            "resolveops.llm.thinking_tokens",
            run_metrics.thinking_tokens,
        )

        span.set_attribute(
            "resolveops.llm.estimated_cost_usd",
            run_metrics.estimated_cost_usd,
        )

        return AgentSessionResult(
            final_text=final_text,
            state=dict(
                session.state
            ),
            metrics=run_metrics,
        )


async def run_structured_agent[TOutput: BaseModel](
    *,
    agent: LlmAgent,
    prompt: str,
    output_type: type[TOutput],
    app_name: str,
    max_llm_calls: int,
    user_id: str = "system",
) -> StructuredAgentResult[TOutput]:
    result = await run_agent_with_state(
        agent=agent,
        prompt=prompt,
        app_name=app_name,
        max_llm_calls=max_llm_calls,
        user_id=user_id,
    )

    if result.final_text is None:
        raise AgentRuntimeError(
            f"Agent {agent.name!r} did not "
            "produce a final text response."
        )

    try:
        output = (
            output_type.model_validate_json(
                result.final_text
            )
        )

    except ValidationError as exc:
        raise AgentRuntimeError(
            f"Agent {agent.name!r} returned "
            "invalid structured output."
        ) from exc

    return StructuredAgentResult(
        output=output,
        metrics=result.metrics,
    )