from uuid import UUID

from app.config import Settings
from app.integrations.billing.client import (
    BillingClient,
)
from app.integrations.crm.client import (
    CRMClient,
)
from app.integrations.errors import (
    IntegrationError,
)
from app.models import (
    AccountStatus,
    ExecutionStatus,
    InvoiceStatus,
    VerificationCheck,
    VerificationResult,
)
from app.state import (
    CaseStage,
    CaseState,
    CaseStateRepository,
)


class VerificationError(RuntimeError):
    """Raised when final verification cannot run."""


class DeterministicVerifier:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: CaseStateRepository,
    ) -> None:
        self._repository = repository

        self._crm = CRMClient(
            base_url=settings.crm_base_url
        )

        self._billing = BillingClient(
            base_url=settings.billing_base_url
        )

    async def run(
        self,
        case_id: UUID | str,
    ) -> CaseState:
        state = self._repository.require(
            case_id
        )

        if (
            state.stage
            is not CaseStage.VERIFYING
        ):
            raise VerificationError(
                "Case is not in VERIFYING stage."
            )

        checks: list[
            VerificationCheck
        ] = []

        tool_calls = 0

        try:
            customer = (
                await self._crm.get_customer(
                    state.customer_id
                )
            )
            tool_calls += 1

            account = (
                await self._crm.get_account(
                    state.customer_id
                )
            )
            tool_calls += 1

        except IntegrationError as exc:
            return self._fail(
                state,
                checks=[
                    VerificationCheck(
                        name="crm_reachable",
                        expected="available",
                        actual=str(exc),
                        passed=False,
                    )
                ],
                tool_calls=tool_calls,
            )

        billing_customer_id = (
            customer.billing_customer_id
        )

        if billing_customer_id is None:
            return self._fail(
                state,
                checks=[
                    VerificationCheck(
                        name=(
                            "billing_customer_id"
                        ),
                        expected="present",
                        actual="missing",
                        passed=False,
                    )
                ],
                tool_calls=tool_calls,
            )

        checks.append(
            VerificationCheck(
                name="crm_account_status",
                expected="ACTIVE",
                actual=account.status.value,
                passed=(
                    account.status
                    is AccountStatus.ACTIVE
                ),
            )
        )

        invoice_ids = (
            _matched_invoice_ids(state)
        )

        if not invoice_ids:
            checks.append(
                VerificationCheck(
                    name="matched_invoice",
                    expected=(
                        "at least one "
                        "successfully matched invoice"
                    ),
                    actual="none",
                    passed=False,
                )
            )

        for invoice_id in invoice_ids:
            try:
                invoice = (
                    await self._billing
                    .get_invoice(
                        billing_customer_id,
                        invoice_id,
                    )
                )
                tool_calls += 1

                checks.append(
                    VerificationCheck(
                        name=(
                            f"invoice_"
                            f"{invoice_id}_status"
                        ),
                        expected="PAID",
                        actual=(
                            invoice.status.value
                        ),
                        passed=(
                            invoice.status
                            is InvoiceStatus.PAID
                        ),
                    )
                )

            except IntegrationError as exc:
                checks.append(
                    VerificationCheck(
                        name=(
                            f"invoice_"
                            f"{invoice_id}_status"
                        ),
                        expected="PAID",
                        actual=str(exc),
                        passed=False,
                    )
                )

        try:
            hold = (
                await self._billing
                .get_account_hold_optional(
                    billing_customer_id
                )
            )
            tool_calls += 1

            hold_active = (
                hold is not None
                and hold.active
            )

            checks.append(
                VerificationCheck(
                    name="billing_hold",
                    expected="inactive",
                    actual=(
                        "active"
                        if hold_active
                        else "inactive"
                    ),
                    passed=not hold_active,
                )
            )

        except IntegrationError as exc:
            checks.append(
                VerificationCheck(
                    name="billing_hold",
                    expected="inactive",
                    actual=str(exc),
                    passed=False,
                )
            )

        success = all(
            check.passed
            for check in checks
        )

        verification = VerificationResult(
            success=success,
            checks=checks,
            summary=(
                "All final-state invariants "
                "passed."
                if success
                else (
                    "One or more final-state "
                    "invariants failed."
                )
            ),
        )

        return self._repository.save(
            state.model_copy(
                update={
                    "verification": verification,
                    "stage": (
                        CaseStage.RESOLVED
                        if success
                        else CaseStage.FAILED
                    ),
                    "tool_calls": (
                        state.tool_calls
                        + tool_calls
                    ),
                }
            )
        )

    def _fail(
        self,
        state: CaseState,
        *,
        checks: list[VerificationCheck],
        tool_calls: int,
    ) -> CaseState:
        verification = VerificationResult(
            success=False,
            checks=checks,
            summary=(
                "Final verification failed."
            ),
        )

        return self._repository.save(
            state.model_copy(
                update={
                    "verification": verification,
                    "stage": CaseStage.FAILED,
                    "tool_calls": (
                        state.tool_calls
                        + tool_calls
                    ),
                }
            )
        )


def _matched_invoice_ids(
    state: CaseState,
) -> list[str]:
    invoice_ids: list[str] = []

    for action in state.executed_actions:
        if (
            action.status
            is not ExecutionStatus.SUCCESS
            or action.tool_name
            != "match_payment"
        ):
            continue

        invoice_id = action.arguments.get(
            "invoice_id"
        )

        if (
            isinstance(invoice_id, str)
            and invoice_id
            not in invoice_ids
        ):
            invoice_ids.append(
                invoice_id
            )

    return invoice_ids