from enum import StrEnum

from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

from app.agents.callbacks import (
    log_after_model,
    log_before_model,
)
from app.agents.model_config import (
    build_generate_content_config,
)
from app.config import Settings


class CasePriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CaseIntakeSummary(BaseModel):
    customer_id: str = Field(
        min_length=1,
        max_length=64,
    )

    issue_type: str = Field(
        min_length=1,
        max_length=100,
    )

    priority: CasePriority

    summary: str = Field(
        min_length=1,
        max_length=500,
    )


def build_smoke_agent(
    settings: Settings,
) -> LlmAgent:
    return LlmAgent(
        name="case_intake_smoke",
        model=settings.adk_model,
        description=(
            "Validates the ResolveOps ADK "
            "and Gemini integration."
        ),
        instruction=(
            "You classify an incoming enterprise "
            "support case. "
            "Extract the customer ID, classify the "
            "issue type, assign a priority, and "
            "write a concise factual summary. "
            "Do not investigate the issue. "
            "Do not propose remediation. "
            "Do not invent facts that are not "
            "present in the case description."
        ),
        output_schema=CaseIntakeSummary,
        output_key="case_intake_summary",
        generate_content_config=(
            build_generate_content_config(
                settings
            )
        ),
        before_model_callback=(
            log_before_model
        ),
        after_model_callback=(
            log_after_model
        ),
    )