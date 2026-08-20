from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import (
    BaseModel,
    model_validator,
)

from app.approvals.service import (
    ApprovalError,
    ApprovalService,
)
from app.auth.google import (
    require_operator,
)
from app.auth.models import (
    AuthenticatedUser,
)
from app.config import get_settings
from app.execution.executor import (
    DeterministicExecutor,
    ExecutionError,
)
from app.models import ApprovalDecision
from app.state import (
    CaseState,
    CaseStateRepository,
    SessionLocal,
)
from app.verification.service import (
    DeterministicVerifier,
    VerificationError,
)

router = APIRouter(
    prefix="/cases",
    tags=["cases"],
)


settings = get_settings()

repository = CaseStateRepository(
    SessionLocal
)

approval_service = ApprovalService(
    repository
)

executor = DeterministicExecutor(
    settings=settings,
    repository=repository,
)

verifier = DeterministicVerifier(
    settings=settings,
    repository=repository,
)


class ApprovalDecisionRequest(
    BaseModel
):
    decision: ApprovalDecision

    @model_validator(mode="after")
    def validate_decision(
        self,
    ) -> "ApprovalDecisionRequest":
        if (
            self.decision
            is ApprovalDecision.PENDING
        ):
            raise ValueError(
                "Human decision must be "
                "APPROVED or REJECTED."
            )

        return self

class CaseMetricsResponse(BaseModel):
    case_id: UUID

    stage: str

    model_calls: int

    tool_calls: int

    input_tokens: int

    tool_input_tokens: int

    output_tokens: int

    thinking_tokens: int

    total_llm_tokens: int

    llm_latency_ms: float

    output_tokens_per_second: float

    estimated_cost_usd: float

    estimated_cost_per_model_call_usd: float

    plan_revision_count: int

    executed_actions: int

    verification_success: bool | None

class CaseListResponse(BaseModel):
    total: int
    items: list[CaseState]


@router.get(
    "",
    response_model=CaseListResponse,
)
async def list_cases(
    customer_id: str | None = None,
    stage: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> CaseListResponse:
    items = repository.list(
        customer_id=customer_id,
        stage=stage,
        limit=limit,
        offset=offset,
    )
    total = repository.count(
        customer_id=customer_id,
        stage=stage,
    )
    return CaseListResponse(
        total=total,
        items=items,
    )


@router.get(
    "/{case_id}",
    response_model=CaseState,
)
async def get_case(
    case_id: UUID,
) -> CaseState:
    try:
        return repository.require(
            case_id
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.post(
    "/{case_id}/approval",
    response_model=CaseState,
)
async def decide_approval(
    case_id: UUID,
    request: ApprovalDecisionRequest,
    user: Annotated[
        AuthenticatedUser,
        Depends(require_operator),
    ],
) -> CaseState:
    try:
        return approval_service.decide(
            case_id=case_id,
            user_id=user.subject,
            decision=request.decision,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ApprovalError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.post(
    "/{case_id}/execute",
    response_model=CaseState,
)
async def execute_case(
    case_id: UUID,
    _: Annotated[
        AuthenticatedUser,
        Depends(require_operator),
    ],
) -> CaseState:
    try:
        return await executor.run(
            case_id
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ExecutionError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

@router.post(
    "/{case_id}/verify",
    response_model=CaseState,
)
async def verify_case(
    case_id: UUID,
    _: Annotated[
        AuthenticatedUser,
        Depends(require_operator),
    ],
) -> CaseState:
    try:
        return await verifier.run(
            case_id
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except VerificationError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

@router.get(
    "/{case_id}/metrics",
    response_model=CaseMetricsResponse,
)
async def get_case_metrics(
    case_id: UUID,
) -> CaseMetricsResponse:
    try:
        state = repository.require(
            case_id
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    total_tokens = (
        state.input_tokens
        + state.tool_input_tokens
        + state.output_tokens
        + state.thinking_tokens
    )

    latency_seconds = (
        state.llm_latency_ms
        / 1000.0
    )

    throughput = (
        0.0
        if latency_seconds == 0
        else (
            state.output_tokens
            / latency_seconds
        )
    )

    cost_per_call = (
        0.0
        if state.model_calls == 0
        else (
            state.estimated_cost_usd
            / state.model_calls
        )
    )

    verification_success = (
        state.verification.success
        if state.verification
        is not None
        else None
    )

    return CaseMetricsResponse(
        case_id=state.case_id,
        stage=state.stage.value,
        model_calls=state.model_calls,
        tool_calls=state.tool_calls,
        input_tokens=state.input_tokens,
        tool_input_tokens=(
            state.tool_input_tokens
        ),
        output_tokens=(
            state.output_tokens
        ),
        thinking_tokens=(
            state.thinking_tokens
        ),
        total_llm_tokens=total_tokens,
        llm_latency_ms=(
            state.llm_latency_ms
        ),
        output_tokens_per_second=(
            throughput
        ),
        estimated_cost_usd=(
            state.estimated_cost_usd
        ),
        estimated_cost_per_model_call_usd=(
            cost_per_call
        ),
        plan_revision_count=(
            state.plan_revision_count
        ),
        executed_actions=len(
            state.executed_actions
        ),
        verification_success=(
            verification_success
        ),
    )