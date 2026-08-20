import json
from uuid import UUID

from app.agents.model_config import (
    configure_adk_environment,
)
from app.agents.planner import (
    PlannerResult,
    build_planner,
    to_resolution_plan,
)
from app.agents.reviewer import (
    ReviewerResult,
    build_reviewer,
    to_plan_review,
)
from app.agents.runtime import (
    run_structured_agent,
)
from app.approvals.service import (
    build_pending_approval,
)
from app.config import Settings
from app.models import (
    ResolutionPlan,
    ReviewVerdict,
)
from app.retrieval.embeddings import (
    GeminiEmbeddingProvider,
)
from app.retrieval.models import (
    PolicySearchResult,
)
from app.retrieval.retriever import (
    PolicyRetriever,
)
from app.state import (
    CaseStage,
    CaseState,
    CaseStateRepository,
)


class PlanningReviewWorkflow:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: CaseStateRepository,
    ) -> None:
        self._settings = settings
        self._repository = repository

        embeddings = GeminiEmbeddingProvider(
            model=settings.embedding_model,
            dimensions=(
                settings.embedding_dimensions
            ),
            api_key=settings.google_api_key,
        )

        self._retriever = PolicyRetriever(
            index_path=(
                settings.policy_index_path
            ),
            embeddings=embeddings,
            top_k=settings.policy_search_top_k,
        )

    async def run(
        self,
        case_id: UUID | str,
        *,
        review_enabled: bool = True,
    ) -> CaseState:
        state = self._repository.require(
            case_id
        )

        if state.stage not in {
            CaseStage.PLANNING,
            CaseStage.REVIEW,
        }:
            return state

        configure_adk_environment(
            self._settings
        )

        # Four transitions are enough for:
        #
        # Planner #1
        # Reviewer #1
        # Planner #2
        # Reviewer #2
        #
        # The explicit bound prevents an
        # accidental reflection loop.
        max_transitions = (
            2
            + 2
            * self._settings.max_plan_revisions
        )

        for _ in range(
            max_transitions
        ):
            state = self._repository.require(
                case_id
            )

            if state.stage is CaseStage.PLANNING:
                state = await self._run_planner(
                    state
                )

                continue

            if state.stage is CaseStage.REVIEW:
                if not review_enabled:
                    return (
                        self
                        ._accept_plan_without_review(
                            state
                        )
                    )

                state = await self._run_reviewer(
                    state
                )

                continue

            return state

        state = self._repository.require(
            case_id
        )

        if state.stage in {
            CaseStage.PLANNING,
            CaseStage.REVIEW,
        }:
            state = self._repository.save(
                state.model_copy(
                    update={
                        "stage": (
                            CaseStage.ESCALATED
                        )
                    }
                )
            )

        return state

    async def _run_planner(
        self,
        state: CaseState,
    ) -> CaseState:
        if state.root_cause is None:
            return self._repository.save(
                state.model_copy(
                    update={
                        "stage": (
                            CaseStage.ESCALATED
                        )
                    }
                )
            )

        policies = await self._get_policies(
            state
        )

        planner = build_planner(
            self._settings
        )

        prompt = _build_planner_prompt(
            state=state,
            policies=policies,
        )

        result = await run_structured_agent(
            agent=planner,
            prompt=prompt,
            output_type=PlannerResult,
            app_name=(
                self._settings.adk_app_name
            ),
            max_llm_calls=(
                self._settings
                .planner_max_llm_calls
            ),
        )

        plan = to_resolution_plan(
            result.output,
            customer_id=state.customer_id,
        )

        updated = state.model_copy(
            update={
                "resolution_plan": plan,
                "review": None,
                "stage": CaseStage.REVIEW,
                "model_calls": (
                    state.model_calls
                    + result.metrics.model_calls
                ),
                "input_tokens": (
                    state.input_tokens
                    + result.metrics.input_tokens
                ),
                "output_tokens": (
                    state.output_tokens
                    + result.metrics.output_tokens
                ),
                "tool_input_tokens": (
                    state.tool_input_tokens
                    + result.metrics.tool_input_tokens
                ),

                "thinking_tokens": (
                    state.thinking_tokens
                    + result.metrics.thinking_tokens
                ),

                "llm_latency_ms": (
                    state.llm_latency_ms
                    + result.metrics.model_latency_ms
                ),

                "estimated_cost_usd": (
                    state.estimated_cost_usd
                    + result.metrics.estimated_cost_usd
                ),
            }
        )

        return self._repository.save(
            updated
        )
    
    def _accept_plan_without_review(
        self,
        state: CaseState,
    ) -> CaseState:
        plan = state.resolution_plan

        if plan is None:
            return self._repository.save(
                state.model_copy(
                    update={
                        "stage": (
                            CaseStage.ESCALATED
                        ),
                        "review": None,
                        "approval": None,
                    }
                )
            )

        next_stage = (
            CaseStage.AWAITING_APPROVAL
            if plan.requires_approval
            else CaseStage.EXECUTING
        )

        approval = (
            build_pending_approval(plan)
            if (
                next_stage
                is CaseStage.AWAITING_APPROVAL
            )
            else None
        )

        return self._repository.save(
            state.model_copy(
                update={
                    "stage": next_stage,
                    "review": None,
                    "approval": approval,
                }
            )
        )

    async def _run_reviewer(
        self,
        state: CaseState,
    ) -> CaseState:
        plan = state.resolution_plan

        if plan is None:
            return self._repository.save(
                state.model_copy(
                    update={
                        "stage": (
                            CaseStage.ESCALATED
                        )
                    }
                )
            )

        policies = await self._get_policies(
            state
        )

        reviewer = build_reviewer(
            self._settings
        )

        prompt = _build_reviewer_prompt(
            state=state,
            plan=plan,
            policies=policies,
        )

        result = await run_structured_agent(
            agent=reviewer,
            prompt=prompt,
            output_type=ReviewerResult,
            app_name=(
                self._settings.adk_app_name
            ),
            max_llm_calls=(
                self._settings
                .reviewer_max_llm_calls
            ),
        )

        review = to_plan_review(
            result.output
        )

        next_stage, revision_count = (
            determine_review_transition(
                verdict=review.verdict,
                requires_approval=(
                    plan.requires_approval
                ),
                revision_count=(
                    state.plan_revision_count
                ),
                max_revisions=(
                    self._settings
                    .max_plan_revisions
                ),
            )
        )

        approval = None

        if (
            next_stage
            is CaseStage.AWAITING_APPROVAL
        ):
            approval = build_pending_approval(
                plan
            )

        updated = state.model_copy(
            update={
                "review": review,
                "stage": next_stage,
                "plan_revision_count": (
                    revision_count
                ),
                "model_calls": (
                    state.model_calls
                    + result.metrics.model_calls
                ),
                "input_tokens": (
                    state.input_tokens
                    + result.metrics.input_tokens
                ),
                "output_tokens": (
                    state.output_tokens
                    + result.metrics.output_tokens
                ),
                "approval": approval,
                "tool_input_tokens": (
                    state.tool_input_tokens
                    + result.metrics.tool_input_tokens
                ),

                "thinking_tokens": (
                    state.thinking_tokens
                    + result.metrics.thinking_tokens
                ),

                "llm_latency_ms": (
                    state.llm_latency_ms
                    + result.metrics.model_latency_ms
                ),

                "estimated_cost_usd": (
                    state.estimated_cost_usd
                    + result.metrics.estimated_cost_usd
                ),
            }
        )

        return self._repository.save(
            updated
        )

    async def _get_policies(
        self,
        state: CaseState,
    ) -> list[PolicySearchResult]:
        query = (
            "What remediation actions, ordering, "
            "approval requirements, and safety "
            "rules apply to this root cause? "
            f"Root cause: {state.root_cause}"
        )

        return await self._retriever.search(
            query=query,
            customer_id=state.customer_id,
        )


def determine_review_transition(
    *,
    verdict: ReviewVerdict,
    requires_approval: bool,
    revision_count: int,
    max_revisions: int,
) -> tuple[CaseStage, int]:
    if verdict is ReviewVerdict.APPROVE:
        next_stage = (
            CaseStage.AWAITING_APPROVAL
            if requires_approval
            else CaseStage.EXECUTING
        )

        return (
            next_stage,
            revision_count,
        )

    if verdict is ReviewVerdict.ESCALATE:
        return (
            CaseStage.ESCALATED,
            revision_count,
        )

    if revision_count >= max_revisions:
        return (
            CaseStage.ESCALATED,
            revision_count,
        )

    return (
        CaseStage.PLANNING,
        revision_count + 1,
    )


def _build_planner_prompt(
    *,
    state: CaseState,
    policies: list[PolicySearchResult],
) -> str:
    payload = {
        "case": {
            "case_id": str(
                state.case_id
            ),
            "customer_id": (
                state.customer_id
            ),
            "description": (
                state.description
            ),
        },
        "root_cause": (
            state.root_cause
        ),
        "evidence": [
            evidence.model_dump(
                mode="json"
            )
            for evidence in state.evidence
        ],
        "relevant_policy": [
            policy.model_dump(
                mode="json"
            )
            for policy in policies
        ],
        "reviewer_feedback": (
            state.review.revision_feedback
            if state.review is not None
            else None
        ),
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )


def _build_reviewer_prompt(
    *,
    state: CaseState,
    plan: ResolutionPlan,
    policies: list[PolicySearchResult],
) -> str:
    payload = {
        "case": {
            "case_id": str(
                state.case_id
            ),
            "customer_id": (
                state.customer_id
            ),
            "description": (
                state.description
            ),
        },
        "root_cause": (
            state.root_cause
        ),
        "evidence": [
            evidence.model_dump(
                mode="json"
            )
            for evidence in state.evidence
        ],
        "plan": plan.model_dump(
            mode="json"
        ),
        "relevant_policy": [
            policy.model_dump(
                mode="json"
            )
            for policy in policies
        ],
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )