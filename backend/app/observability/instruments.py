from opentelemetry import metrics

_meter = metrics.get_meter(
    "resolveops"
)


_llm_calls = _meter.create_counter(
    "resolveops.llm.calls"
)

_llm_input_tokens = (
    _meter.create_counter(
        "resolveops.llm.input_tokens"
    )
)

_llm_output_tokens = (
    _meter.create_counter(
        "resolveops.llm.output_tokens"
    )
)

_llm_thinking_tokens = (
    _meter.create_counter(
        "resolveops.llm.thinking_tokens"
    )
)

_llm_cost = _meter.create_counter(
    "resolveops.llm.estimated_cost_usd"
)

_llm_latency = _meter.create_histogram(
    "resolveops.llm.latency_ms",
    unit="ms",
)

_tool_calls = _meter.create_counter(
    "resolveops.tool.calls"
)

_tool_errors = _meter.create_counter(
    "resolveops.tool.errors"
)

_tool_latency = _meter.create_histogram(
    "resolveops.tool.latency_ms",
    unit="ms",
)


def record_llm_call(
    *,
    agent_name: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    thinking_tokens: int,
    cost_usd: float,
    latency_ms: float,
) -> None:
    attributes = {
        "resolveops.agent.name": (
            agent_name
        ),
        "gen_ai.request.model": model,
    }

    _llm_calls.add(
        1,
        attributes,
    )

    _llm_input_tokens.add(
        input_tokens,
        attributes,
    )

    _llm_output_tokens.add(
        output_tokens,
        attributes,
    )

    _llm_thinking_tokens.add(
        thinking_tokens,
        attributes,
    )

    _llm_cost.add(
        cost_usd,
        attributes,
    )

    _llm_latency.record(
        latency_ms,
        attributes,
    )


def record_tool_call(
    *,
    tool_name: str,
    latency_ms: float,
    success: bool,
) -> None:
    attributes = {
        "resolveops.tool.name": (
            tool_name
        ),
    }

    _tool_calls.add(
        1,
        attributes,
    )

    _tool_latency.record(
        latency_ms,
        attributes,
    )

    if not success:
        _tool_errors.add(
            1,
            attributes,
        )