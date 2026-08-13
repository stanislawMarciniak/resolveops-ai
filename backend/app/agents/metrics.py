from dataclasses import dataclass
from typing import Protocol

from pydantic import Field

from app.models.base import DomainModel
from app.observability.cost import (
    estimate_llm_cost_usd,
)


class UsageMetadataLike(Protocol):
    prompt_token_count: int | None
    candidates_token_count: int | None
    thoughts_token_count: int | None
    tool_use_prompt_token_count: int | None
    total_token_count: int | None


class AgentRunMetrics(DomainModel):
    model_calls: int = Field(
        ge=0,
    )

    input_tokens: int = Field(
        ge=0,
    )

    tool_input_tokens: int = Field(
        ge=0,
    )

    output_tokens: int = Field(
        ge=0,
    )

    thinking_tokens: int = Field(
        ge=0,
    )

    total_tokens: int = Field(
        ge=0,
    )

    latency_ms: float = Field(
        ge=0.0,
    )

    model_latency_ms: float = Field(
        ge=0.0,
    )

    output_tokens_per_second: float = (
        Field(
            ge=0.0,
        )
    )

    estimated_cost_usd: float = Field(
        ge=0.0,
    )


@dataclass
class UsageAccumulator:
    model_calls: int = 0
    input_tokens: int = 0
    tool_input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    total_tokens: int = 0

    def add(
        self,
        usage: UsageMetadataLike,
    ) -> None:
        self.model_calls += 1

        self.input_tokens += (
            usage.prompt_token_count or 0
        )

        self.tool_input_tokens += (
            usage
            .tool_use_prompt_token_count
            or 0
        )

        self.output_tokens += (
            usage.candidates_token_count or 0
        )

        self.thinking_tokens += (
            usage.thoughts_token_count or 0
        )

        self.total_tokens += (
            usage.total_token_count or 0
        )

    def build(
        self,
        *,
        latency_ms: float,
        model_latency_ms: float,
        input_cost_per_million: float,
        output_cost_per_million: float,
    ) -> AgentRunMetrics:
        latency_seconds = (
            model_latency_ms / 1000.0
        )

        throughput = (
            0.0
            if latency_seconds == 0
            else (
                self.output_tokens
                / latency_seconds
            )
        )

        cost = estimate_llm_cost_usd(
            prompt_tokens=(
                self.input_tokens
            ),
            tool_input_tokens=(
                self.tool_input_tokens
            ),
            output_tokens=(
                self.output_tokens
            ),
            thinking_tokens=(
                self.thinking_tokens
            ),
            input_cost_per_million=(
                input_cost_per_million
            ),
            output_cost_per_million=(
                output_cost_per_million
            ),
        )

        return AgentRunMetrics(
            model_calls=self.model_calls,
            input_tokens=self.input_tokens,
            tool_input_tokens=(
                self.tool_input_tokens
            ),
            output_tokens=(
                self.output_tokens
            ),
            thinking_tokens=(
                self.thinking_tokens
            ),
            total_tokens=self.total_tokens,
            latency_ms=latency_ms,
            model_latency_ms=(
                model_latency_ms
            ),
            output_tokens_per_second=(
                throughput
            ),
            estimated_cost_usd=cost,
        )