def estimate_llm_cost_usd(
    *,
    prompt_tokens: int,
    tool_input_tokens: int,
    output_tokens: int,
    thinking_tokens: int,
    input_cost_per_million: float,
    output_cost_per_million: float,
) -> float:
    billable_input = (
        prompt_tokens
        + tool_input_tokens
    )

    billable_output = (
        output_tokens
        + thinking_tokens
    )

    input_cost = (
        billable_input
        / 1_000_000
        * input_cost_per_million
    )

    output_cost = (
        billable_output
        / 1_000_000
        * output_cost_per_million
    )

    return input_cost + output_cost