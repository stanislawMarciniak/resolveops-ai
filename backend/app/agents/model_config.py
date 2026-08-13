import os

from google.genai import types

from app.config import Settings

RETRIABLE_HTTP_STATUS_CODES = [
    408,
    429,
    500,
    502,
    503,
    504,
]


def configure_adk_environment(
    settings: Settings,
) -> None:
    os.environ["GOOGLE_API_KEY"] = (
        settings.google_api_key
    )


def build_generate_content_config(
    settings: Settings,
) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        temperature=(
            settings.model_temperature
        ),
        http_options=types.HttpOptions(
            timeout=settings.model_timeout_ms,
            retry_options=types.HttpRetryOptions(
                attempts=(
                    settings.model_retry_attempts
                ),
                initial_delay=1.0,
                max_delay=8.0,
                http_status_codes=(
                    RETRIABLE_HTTP_STATUS_CODES
                ),
            ),
        ),
    )