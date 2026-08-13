import pytest
from app.observability.cost import (
    estimate_llm_cost_usd,
)


def test_estimate_llm_cost() -> None:
    cost = estimate_llm_cost_usd(
        prompt_tokens=1_000_000,
        tool_input_tokens=0,
        output_tokens=1_000_000,
        thinking_tokens=0,
        input_cost_per_million=1.50,
        output_cost_per_million=7.50,
    )

    assert cost == pytest.approx(
        9.0
    )


def test_thinking_tokens_are_output_cost() -> None:
    cost = estimate_llm_cost_usd(
        prompt_tokens=0,
        tool_input_tokens=0,
        output_tokens=0,
        thinking_tokens=1_000_000,
        input_cost_per_million=1.50,
        output_cost_per_million=7.50,
    )

    assert cost == pytest.approx(
        7.50
    )