from app.agents.model_config import (
    build_generate_content_config,
)
from app.agents.smoke_agent import (
    CaseIntakeSummary,
    build_smoke_agent,
)
from app.config import Settings


def test_smoke_agent_configuration() -> None:
    settings = Settings(
        _env_file=None, # pyright: ignore[reportCallIssue]
        google_api_key="test-key",
    )

    agent = build_smoke_agent(
        settings
    )

    assert agent.name == "case_intake_smoke"

    assert (
        agent.model
        == "gemini-3.6-flash"
    )

    assert (
        agent.output_schema
        is CaseIntakeSummary
    )

    assert (
        agent.output_key
        == "case_intake_summary"
    )

    assert agent.tools == []

def test_model_configuration() -> None:
    settings = Settings(
        _env_file=None, # pyright: ignore[reportCallIssue]
        google_api_key="test-key",
        model_temperature=0.2,
        model_timeout_ms=20_000,
        model_retry_attempts=4,
    )

    config = (
        build_generate_content_config(
            settings
        )
    )

    assert config.temperature == 0.2

    assert (
        config.http_options
        is not None
    )

    assert (
        config.http_options.timeout
        == 20_000
    )

    assert (
        config.http_options.retry_options
        is not None
    )

    assert (
        config
        .http_options
        .retry_options
        .attempts
        == 4
    )