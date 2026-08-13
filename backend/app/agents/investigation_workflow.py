from typing import Any
from uuid import UUID

from app.agents.case_manager import (
    build_case_manager,
)
from app.agents.data_readiness import (
    assess_data_readiness,
)
from app.agents.investigator import (
    InvestigationOutcome,
    InvestigationResult,
    build_investigator,
)
from app.agents.model_config import (
    configure_adk_environment,
)
from app.agents.runtime import (
    AgentRuntimeError,
    run_agent_with_state,
)
from app.config import Settings
from app.integrations.billing.client import (
    BillingClient,
)
from app.integrations.crm.client import (
    CRMClient,
)
from app.state import (
    CaseStage,
    CaseState,
    CaseStateRepository,
)


class InvestigationWorkflow:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: CaseStateRepository,
    ) -> None:
        self._settings = settings
        self._repository = repository

        self._crm = CRMClient(
            base_url=(
                settings.crm_base_url
            )
        )

        self._billing = BillingClient(
            base_url=(
                settings.billing_base_url
            )
        )

    async def run(
        self,
        case_id: UUID | str,
    ) -> CaseState:
        state = self._repository.require(
            case_id
        )

        if state.stage is CaseStage.PLANNING:
            return state

        if state.stage not in {
            CaseStage.NEW,
            CaseStage.INVESTIGATING,
        }:
            raise ValueError(
                "Investigation cannot run "
                f"from stage {state.stage}."
            )

        state = self._repository.save(
            state.model_copy(
                update={
                    "stage": (
                        CaseStage
                        .INVESTIGATING
                    )
                }
            )
        )

        try:
            return await self._run(
                state
            )

        except Exception:
            self._repository.save(
                state.model_copy(
                    update={
                        "stage": (
                            CaseStage.FAILED
                        )
                    }
                )
            )

            raise

    async def _run(
        self,
        state: CaseState,
    ) -> CaseState:
        readiness = (
            await assess_data_readiness(
                case=state,
                crm=self._crm,
                billing=self._billing,
            )
        )

        configure_adk_environment(
            self._settings
        )

        investigator, toolset = (
            build_investigator(
                self._settings
            )
        )

        manager = build_case_manager(
            settings=self._settings,
            investigator=investigator,
        )

        case_context = {
            "case_id": str(
                state.case_id
            ),
            "customer_id": (
                state.customer_id
            ),
            "description": (
                state.description
            ),
        }

        try:
            run_result = (
                await run_agent_with_state(
                    agent=manager,
                    prompt=(
                        "Investigate the current "
                        "enterprise case."
                    ),
                    app_name=(
                        self._settings
                        .adk_app_name
                    ),
                    max_llm_calls=(
                        self._settings
                        .investigation_max_llm_calls
                    ),
                    initial_state={
                        "case_context": (
                            _to_json(
                                case_context
                            )
                        ),
                        "data_readiness_report": (
                            readiness
                            .model_dump_json()
                        ),
                        "investigator_tool_calls": 0,
                        "investigator_repeat_count": 0,
                    },
                )
            )

        finally:
            await toolset.close()

        raw_result = (
            run_result.state.get(
                "investigation_result"
            )
        )

        investigation = (
            _parse_investigation_result(
                raw_result
            )
        )

        tool_calls = int(
            run_result.state.get(
                "investigator_tool_calls",
                0,
            )
        )

        if (
            investigation.outcome
            is InvestigationOutcome
            .ROOT_CAUSE_FOUND
        ):
            next_stage = (
                CaseStage.PLANNING
            )
        else:
            next_stage = (
                CaseStage.ESCALATED
            )

        updated = state.model_copy(
            update={
                "evidence": (
                    investigation.evidence
                ),
                "hypotheses": (
                    investigation.hypotheses
                ),
                "root_cause": (
                    investigation.root_cause
                ),
                "stage": next_stage,
                "model_calls": (
                    state.model_calls
                    + run_result
                    .metrics
                    .model_calls
                ),
                "tool_calls": (
                    state.tool_calls
                    + tool_calls
                ),
                "input_tokens": (
                    state.input_tokens
                    + run_result
                    .metrics
                    .input_tokens
                ),
                "output_tokens": (
                    state.output_tokens
                    + run_result
                    .metrics
                    .output_tokens
                ),
                "tool_input_tokens": (
                    state.tool_input_tokens
                    + run_result
                    .metrics
                    .tool_input_tokens
                ),

                "thinking_tokens": (
                    state.thinking_tokens
                    + run_result
                    .metrics
                    .thinking_tokens
                ),

                "llm_latency_ms": (
                    state.llm_latency_ms
                    + run_result
                    .metrics
                    .model_latency_ms
                ),

                "estimated_cost_usd": (
                    state.estimated_cost_usd
                    + run_result
                    .metrics
                    .estimated_cost_usd
                ),
            }
        )

        return self._repository.save(
            updated
        )


def _parse_investigation_result(
    value: Any,
) -> InvestigationResult:
    if isinstance(value, str):
        return (
            InvestigationResult
            .model_validate_json(value)
        )

    if isinstance(value, dict):
        return (
            InvestigationResult
            .model_validate(value)
        )

    raise AgentRuntimeError(
        "Investigator did not store a valid "
        "investigation_result in ADK state."
    )


def _to_json(
    value: dict[str, Any],
) -> str:
    import json

    return json.dumps(
        value,
        ensure_ascii=False,
    )