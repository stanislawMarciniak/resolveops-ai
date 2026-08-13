from google.adk.agents import LlmAgent
from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

from app.agents.callbacks import (
    log_after_model,
    log_before_model,
)
from app.agents.model_config import (
    build_generate_content_config,
)
from app.config import Settings
from app.models import (
    PlanReview,
    ReviewVerdict,
)


class ReviewerResult(BaseModel):
    verdict: ReviewVerdict

    summary: str = Field(
        min_length=1,
        max_length=2_000,
    )

    issues: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    revision_feedback: str | None = Field(
        default=None,
        max_length=2_000,
    )

    @model_validator(mode="after")
    def validate_revision_feedback(
        self,
    ) -> "ReviewerResult":
        if (
            self.verdict
            is ReviewVerdict.REVISE
            and not self.revision_feedback
        ):
            raise ValueError(
                "REVISE requires "
                "revision_feedback."
            )

        return self


def build_reviewer(
    settings: Settings,
) -> LlmAgent:
    return LlmAgent(
        name="reviewer",
        model=settings.adk_model,
        mode="chat",
        description=(
            "Critically reviews remediation "
            "plans for evidence, policy, and "
            "safety problems."
        ),
        instruction="""
You are the ResolveOps Reviewer.

You are an independent critic and safety
reviewer.

You do not investigate the case.
You do not execute tools.
You do not create a replacement plan.

Review the supplied:
- case,
- evidence,
- root cause,
- remediation plan,
- policy excerpts.

IMPORTANT TOOL CONTRACT:

ResolveOps enterprise tools operate on the
canonical CRM customer ID.

For this case:

case.customer_id is the authoritative customer
identifier for all PlannedAction customer_id
arguments.

Billing customer IDs such as "000018392" are
legacy integration identifiers used internally
by the Billing adapter.

They must NOT replace the canonical customer ID
in PlannedAction arguments.

For example:

case.customer_id = "ACME"

and evidence may contain:

billing_customer_id = "000018392"

The correct tool argument is still:

customer_id = "ACME"

ResolveOps deterministically maps:

ACME -> 000018392

inside the integration layer.

Therefore:
- match_payment.customer_id must equal
  case.customer_id.
- remove_account_hold.customer_id must equal
  case.customer_id.
- Do not request replacement of a canonical CRM
  customer ID with a billing customer ID.

Check:

1. Evidence
   Is the root cause supported by evidence?

2. Causal consistency
   Do the proposed actions actually address
   the diagnosed root cause?

3. Tool arguments
   Are payment and invoice IDs supported by
   evidence?
   Does customer_id equal case.customer_id?

4. Ordering
   Are dependent mutation actions in the
   correct order?

5. Policy
   Is the plan consistent with supplied policy?

6. Unsupported claims
   Does the plan assume facts not present in
   evidence?

7. Safety
   Are write operations correctly marked as
   requiring approval according to the plan?

Execution model:

The remediation plan intentionally contains
mutation actions only.

Do not require read or verification tools such
as get_invoice to appear as PlannedActions.

ResolveOps uses a deterministic Executor that
performs mandatory read-after-write checks.

In particular:

match_payment
    ↓
Executor retrieves the affected invoice
    ↓
invoice status MUST be PAID
    ↓
only then may remove_account_hold execute.

Therefore a plan containing:

1. match_payment
2. remove_account_hold

has correct action ordering as long as the
evidence and policies support those mutations.

Do not return REVISE merely because get_invoice
is not explicitly listed between them.

Return:

APPROVE
- Plan is evidence-grounded, policy-compliant,
  and safe to present for human approval.

REVISE
- Plan has a correctable planning problem.
- Explain exactly what Planner must change in
  revision_feedback.

ESCALATE
- Evidence is insufficient or contradictory,
  or no safe policy-compliant remediation can
  be established.

Do not approve merely because a plan looks
plausible.

Return only the structured ReviewerResult.
""".strip(),
        output_schema=ReviewerResult,
        output_key="reviewer_result",
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


def to_plan_review(
    result: ReviewerResult,
) -> PlanReview:
    return PlanReview(
        verdict=result.verdict,
        summary=result.summary,
        issues=result.issues,
        revision_feedback=(
            result.revision_feedback
        ),
    )