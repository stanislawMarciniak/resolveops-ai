from datetime import UTC, datetime
from uuid import UUID

from mcp import ClientSession
from pydantic import ValidationError

from app.approvals.service import (
    compute_plan_digest,
)
from app.config import Settings
from app.execution.mcp_client import (
    call_tool_json,
    open_mcp_session,
)
from app.execution.schemas import (
    MatchPaymentArguments,
    RemoveAccountHoldArguments,
)
from app.integrations.billing.results import (
    InvoiceLookupResult,
)
from app.mcp.metadata import (
    ToolAccess,
    get_tool_definition,
)
from app.mcp.schemas import OperationResult
from app.models import (
    ApprovalDecision,
    ExecutedAction,
    ExecutionStatus,
    InvoiceStatus,
    PlannedAction,
    ResolutionPlan,
    ReviewVerdict,
)
from app.state import (
    CaseStage,
    CaseState,
    CaseStateRepository,
)


class ExecutionError(RuntimeError):
    """Raised when deterministic execution cannot safely continue."""


def utc_now() -> datetime:
    return datetime.now(UTC)


def validate_execution_authorization(
    state: CaseState,
) -> ResolutionPlan:
    if (
        state.stage
        is not CaseStage.EXECUTING
    ):
        raise ExecutionError(
            "Case is not in EXECUTING stage."
        )

    plan = state.resolution_plan

    if plan is None:
        raise ExecutionError(
            "Case does not have a "
            "resolution plan."
        )

    if (
        state.review is None
        or state.review.verdict
        is not ReviewVerdict.APPROVE
    ):
        raise ExecutionError(
            "Resolution plan is not "
            "Reviewer-approved."
        )

    if plan.requires_approval:
        approval = state.approval

        if approval is None:
            raise ExecutionError(
                "Plan requires approval but "
                "no approval exists."
            )

        if (
            approval.decision
            is not ApprovalDecision.APPROVED
        ):
            raise ExecutionError(
                "Plan has not been "
                "human-approved."
            )

        current_digest = (
            compute_plan_digest(plan)
        )

        if (
            approval.plan_digest
            != current_digest
        ):
            raise ExecutionError(
                "Human approval belongs to "
                "a different plan version."
            )

    return plan


def validate_planned_action(
    *,
    state: CaseState,
    action: PlannedAction,
) -> dict[str, str]:
    try:
        definition = get_tool_definition(
            action.tool_name
        )

    except KeyError as exc:
        raise ExecutionError(
            f"Unknown planned tool: "
            f"{action.tool_name}"
        ) from exc

    if (
        definition.access
        is not ToolAccess.WRITE
    ):
        raise ExecutionError(
            f"Executor refuses non-WRITE "
            f"planned tool "
            f"{action.tool_name!r}."
        )

    if action.risk is not definition.risk:
        raise ExecutionError(
            f"Risk metadata mismatch for "
            f"{action.tool_name!r}."
        )

    if (
        action.requires_approval
        != definition.requires_approval
    ):
        raise ExecutionError(
            f"Approval metadata mismatch for "
            f"{action.tool_name!r}."
        )

    evidence_ids = {
        evidence.evidence_id
        for evidence in state.evidence
    }

    unknown_evidence = (
        set(action.evidence_ids)
        - evidence_ids
    )

    if unknown_evidence:
        raise ExecutionError(
            "Planned action references "
            "unknown evidence IDs: "
            + ", ".join(
                sorted(
                    unknown_evidence
                )
            )
        )

    try:
        if (
            action.tool_name
            == "match_payment"
        ):
            match_args = (
                MatchPaymentArguments
                .model_validate(
                    action.arguments
                )
            )

            arguments = (
                match_args.model_dump()
            )

        elif (
            action.tool_name
            == "remove_account_hold"
        ):
            hold_args = (
                RemoveAccountHoldArguments
                .model_validate(
                    action.arguments
                )
            )

            arguments = (
                hold_args.model_dump()
            )

        else:
            raise ExecutionError(
                "Tool is WRITE-classified "
                "but Executor has no "
                "implementation for "
                f"{action.tool_name!r}."
            )

    except ValidationError as exc:
        raise ExecutionError(
            f"Invalid arguments for "
            f"{action.tool_name!r}."
        ) from exc

    customer_id = arguments.get(
        "customer_id"
    )

    if customer_id != state.customer_id:
        raise ExecutionError(
            "Planned customer ID does not "
            "match CaseState customer ID."
        )

    return {
        key: str(value)
        for key, value
        in arguments.items()
    }


class DeterministicExecutor:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: CaseStateRepository,
    ) -> None:
        self._settings = settings
        self._repository = repository

    async def run(
        self,
        case_id: UUID | str,
    ) -> CaseState:
        state = self._repository.require(
            case_id
        )

        plan = (
            validate_execution_authorization(
                state
            )
        )

        _validate_execution_prefix(
            state,
            plan,
        )

        async with open_mcp_session(
            self._settings.mcp_server_url
        ) as session:
            for index, action in enumerate(
                plan.actions
            ):
                state = (
                    self._repository.require(
                        case_id
                    )
                )

                if (
                    index
                    < len(
                        state.executed_actions
                    )
                ):
                    continue

                arguments = (
                    validate_planned_action(
                        state=state,
                        action=action,
                    )
                )

                try:
                    state = await self._execute_action(
                        state=state,
                        plan=plan,
                        action_index=index,
                        action=action,
                        arguments=arguments,
                        session=session,
                    )

                except Exception as exc:
                    failed_action = (
                        ExecutedAction(
                            tool_name=(
                                action.tool_name
                            ),
                            arguments=(
                                action.arguments
                            ),
                            status=(
                                ExecutionStatus
                                .FAILED
                            ),
                            started_at=utc_now(),
                            completed_at=utc_now(),
                            error=str(exc),
                        )
                    )

                    self._repository.save(
                        state.model_copy(
                            update={
                                "executed_actions": [
                                    *state
                                    .executed_actions,
                                    failed_action,
                                ],
                                "stage": (
                                    CaseStage.FAILED
                                ),
                            }
                        )
                    )

                    raise ExecutionError(
                        "Execution failed for "
                        f"{action.tool_name!r}."
                    ) from exc

        state = self._repository.require(
            case_id
        )

        return self._repository.save(
            state.model_copy(
                update={
                    "stage": (
                        CaseStage.VERIFYING
                    )
                }
            )
        )

    async def _execute_action(
        self,
        *,
        state: CaseState,
        plan: ResolutionPlan,
        action_index: int,
        action: PlannedAction,
        arguments: dict[str, str],
        session: ClientSession,
    ) -> CaseState:
        tool_calls = 0

        if (
            action.tool_name
            == "remove_account_hold"
        ):
            tool_calls += (
                await _verify_paid_invoice_before_hold_removal(
                    session=session,
                    state=state,
                    plan=plan,
                    action_index=(
                        action_index
                    ),
                )
            )

        started_at = utc_now()

        tool_calls += 1

        payload = await call_tool_json(
            session,
            tool_name=action.tool_name,
            arguments=arguments,
        )

        result = (
            OperationResult.model_validate(
                payload
            )
        )

        if not result.success:
            raise ExecutionError(
                f"{action.tool_name} "
                "reported failure."
            )

        executed = ExecutedAction(
            tool_name=action.tool_name,
            arguments=action.arguments,
            status=ExecutionStatus.SUCCESS,
            started_at=started_at,
            completed_at=utc_now(),
            result_summary=result.message,
        )

        return self._repository.save(
            state.model_copy(
                update={
                    "executed_actions": [
                        *state.executed_actions,
                        executed,
                    ],
                    "tool_calls": (
                        state.tool_calls
                        + tool_calls
                    ),
                }
            )
        )


async def _verify_paid_invoice_before_hold_removal(
    *,
    session: ClientSession,
    state: CaseState,
    plan: ResolutionPlan,
    action_index: int,
) -> int:
    invoice_ids = [
        str(
            action.arguments[
                "invoice_id"
            ]
        )
        for action
        in plan.actions[:action_index]
        if (
            action.tool_name
            == "match_payment"
            and action.arguments.get(
                "invoice_id"
            )
            is not None
        )
    ]

    if not invoice_ids:
        raise ExecutionError(
            "Cannot remove account hold "
            "without a preceding payment "
            "matching action."
        )

    for tool_calls, invoice_id in enumerate(
        reversed(invoice_ids),
        start=1,
    ):
        payload = await call_tool_json(
            session,
            tool_name="get_invoice",
            arguments={
                "customer_id": (
                    state.customer_id
                ),
                "invoice_id": invoice_id,
            },
        )

        lookup = (
            InvoiceLookupResult
            .model_validate(payload)
        )

        if (
            lookup.invoice.status
            is InvoiceStatus.PAID
        ):
            return tool_calls

    raise ExecutionError(
        "Policy precondition failed: "
        "invoice was not verified as PAID "
        "before account hold removal."
    )


def _validate_execution_prefix(
    state: CaseState,
    plan: ResolutionPlan,
) -> None:
    if (
        len(state.executed_actions)
        > len(plan.actions)
    ):
        raise ExecutionError(
            "Executed action history is "
            "longer than the current plan."
        )

    for index, executed in enumerate(
        state.executed_actions
    ):
        planned = plan.actions[index]

        if (
            executed.status
            is not ExecutionStatus.SUCCESS
        ):
            raise ExecutionError(
                "Execution history contains "
                "a non-successful action."
            )

        if (
            executed.tool_name
            != planned.tool_name
            or executed.arguments
            != planned.arguments
        ):
            raise ExecutionError(
                "Execution history does not "
                "match the current plan."
            )