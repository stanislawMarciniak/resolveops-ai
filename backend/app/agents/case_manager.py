from google.adk.agents import LlmAgent

from app.agents.callbacks import (
    log_after_model,
    log_before_model,
)
from app.agents.model_config import (
    build_generate_content_config,
)
from app.config import Settings


def build_case_manager(
    *,
    settings: Settings,
    investigator: LlmAgent,
) -> LlmAgent:
    return LlmAgent(
        name="case_manager",
        model=settings.adk_model,
        description=(
            "Coordinates the ResolveOps "
            "enterprise case workflow."
        ),
        instruction="""
You are the ResolveOps Case Manager.

You are a supervisor, not an investigator.

Current case:
{case_context}

Your current workflow stage is INVESTIGATING.

Delegate the investigation to the
'investigator' sub-agent.

Do not:
- diagnose the case yourself,
- call enterprise tools yourself,
- propose remediation,
- execute any action.

The Investigator is responsible for gathering
evidence, testing hypotheses, and producing
the structured investigation result.

Delegate exactly one investigation task.
After the Investigator returns, acknowledge
that the investigation stage has completed
and return control to the application.
""".strip(),
        sub_agents=[
            investigator,
        ],
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