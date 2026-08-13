from dataclasses import dataclass

import pytest
from app.agents.metrics import (
    UsageAccumulator,
)


@dataclass
class FakeUsage:
    prompt_token_count: int | None
    candidates_token_count: int | None
    thoughts_token_count: int | None
    tool_use_prompt_token_count: int | None
    total_token_count: int | None

def test_usage_accumulator() -> None:
    accumulator = UsageAccumulator()

    accumulator.add(
        FakeUsage(
          prompt_token_count=100,
          candidates_token_count=20,
          thoughts_token_count=10,
          tool_use_prompt_token_count=5,
          total_token_count=120,
      )
    )

    accumulator.add(
        FakeUsage(
            prompt_token_count=150,
            candidates_token_count=30,
            thoughts_token_count=15,
            tool_use_prompt_token_count=7,
            total_token_count=180,
        )
    )

    metrics = accumulator.build(
        latency_ms=2000.0,
        model_latency_ms=1000.0,
        input_cost_per_million=1.50,
        output_cost_per_million=7.50,
    )

    assert metrics.model_calls == 2

    assert metrics.input_tokens == 250
    assert metrics.output_tokens == 50
    assert metrics.total_tokens == 300

    assert metrics.latency_ms == 2000.0

    assert (
        metrics.output_tokens_per_second
        == pytest.approx(50.0)
    )


def test_missing_usage_values_are_zero() -> None:
    accumulator = UsageAccumulator()

    accumulator.add(
        FakeUsage(
            prompt_token_count=None,
            candidates_token_count=None,
            thoughts_token_count=None,
            tool_use_prompt_token_count=None,
            total_token_count=None,
        )
    )

    metrics = accumulator.build(
            latency_ms=1000.0,
            model_latency_ms=1000.0,
            input_cost_per_million=1.50,
            output_cost_per_million=7.50,
        )

    assert metrics.model_calls == 1

    assert metrics.input_tokens == 0
    assert metrics.output_tokens == 0
    assert metrics.total_tokens == 0