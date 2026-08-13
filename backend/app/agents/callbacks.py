import logging
from time import perf_counter

from google.adk.agents.callback_context import (
    CallbackContext,
)
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

from app.config import get_settings
from app.observability.cost import (
    estimate_llm_cost_usd,
)
from app.observability.instruments import (
    record_llm_call,
)

logger = logging.getLogger(__name__)

MODEL_STARTED_AT_KEY = (
    "_obs_model_started_at"
)

MODEL_LATENCY_MS_KEY = (
    "_obs_model_latency_ms"
)

def log_before_model(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> LlmResponse | None:
    logger.info(
        "llm.request agent=%s content_items=%d",
        callback_context.agent_name,
        len(llm_request.contents or []),
    )
    callback_context.state[
        MODEL_STARTED_AT_KEY
    ] = perf_counter()

    return None


def log_after_model(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse | None:
    started_at = (
        callback_context.state.get(
            MODEL_STARTED_AT_KEY
        )
    )

    latency_ms = 0.0

    if isinstance(
        started_at,
        int | float,
    ):
        latency_ms = (
            perf_counter()
            - started_at
        ) * 1000.0

    previous_latency = (
        callback_context.state.get(
            MODEL_LATENCY_MS_KEY,
            0.0,
        )
    )

    if not isinstance(
        previous_latency,
        int | float,
    ):
        previous_latency = 0.0

    callback_context.state[
        MODEL_LATENCY_MS_KEY
    ] = (
        previous_latency
        + latency_ms
    )
    usage = llm_response.usage_metadata

    if usage is None:
        logger.info(
            "llm.response agent=%s "
            "usage_metadata=missing",
            callback_context.agent_name,
        )

        return None

    settings = get_settings()

    input_tokens = (
        usage.prompt_token_count or 0
    )

    tool_input_tokens = (
        usage.tool_use_prompt_token_count
        or 0
    )

    output_tokens = (
        usage.candidates_token_count or 0
    )

    thinking_tokens = (
        usage.thoughts_token_count or 0
    )

    cost = estimate_llm_cost_usd(
        prompt_tokens=input_tokens,
        tool_input_tokens=(
            tool_input_tokens
        ),
        output_tokens=output_tokens,
        thinking_tokens=thinking_tokens,
        input_cost_per_million=(
            settings
            .model_input_cost_per_million
        ),
        output_cost_per_million=(
            settings
            .model_output_cost_per_million
        ),
    )

    record_llm_call(
        agent_name=(
            callback_context.agent_name
        ),
        model=settings.adk_model,
        input_tokens=(
            input_tokens
            + tool_input_tokens
        ),
        output_tokens=output_tokens,
        thinking_tokens=thinking_tokens,
        cost_usd=cost,
        latency_ms=latency_ms,
    )

    logger.info(
        "llm.response "
        "agent=%s "
        "input_tokens=%s "
        "output_tokens=%s "
        "total_tokens=%s",
        callback_context.agent_name,
        usage.prompt_token_count or 0,
        usage.candidates_token_count or 0,
        usage.total_token_count or 0,
    )

    return None