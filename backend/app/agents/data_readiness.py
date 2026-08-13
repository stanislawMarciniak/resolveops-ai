import re
from enum import StrEnum
from typing import Protocol

from pydantic import Field

from app.integrations.billing.adapter import (
    LegacyBillingError,
    normalize_invoice_id,
)
from app.integrations.errors import (
    IntegrationError,
)
from app.models import (
    Account,
    AccountHold,
    AccountStatus,
    Customer,
    Invoice,
    InvoiceStatus,
)
from app.models.base import DomainModel
from app.state import CaseState

INVOICE_REFERENCE_PATTERN = re.compile(
    r"\bINV[\s-]?\d+\b",
    flags=re.IGNORECASE,
)


class CRMReader(Protocol):
    async def get_customer(
        self,
        customer_id: str,
    ) -> Customer:
        ...

    async def get_account(
        self,
        customer_id: str,
    ) -> Account:
        ...


class BillingReader(Protocol):
    async def get_invoice(
        self,
        billing_customer_id: str,
        invoice_id: str,
    ) -> Invoice:
        ...

    async def get_account_hold_optional(
        self,
        billing_customer_id: str,
    ) -> AccountHold | None:
        ...


class DataWarningSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class DataWarningCode(StrEnum):
    CRM_LOOKUP_FAILED = "CRM_LOOKUP_FAILED"

    MISSING_BILLING_ID = (
        "MISSING_BILLING_ID"
    )

    NO_INVOICE_REFERENCE = (
        "NO_INVOICE_REFERENCE"
    )

    INVALID_INVOICE_ID = (
        "INVALID_INVOICE_ID"
    )

    INVOICE_LOOKUP_FAILED = (
        "INVOICE_LOOKUP_FAILED"
    )

    CUSTOMER_INVOICE_MISMATCH = (
        "CUSTOMER_INVOICE_MISMATCH"
    )

    CRM_BILLING_STATUS_CONFLICT = (
        "CRM_BILLING_STATUS_CONFLICT"
    )

    BILLING_HOLD_LOOKUP_FAILED = (
        "BILLING_HOLD_LOOKUP_FAILED"
    )


class DataReadinessWarning(DomainModel):
    code: DataWarningCode

    severity: DataWarningSeverity

    message: str = Field(
        min_length=1,
        max_length=500,
    )


class DataReadinessReport(DomainModel):
    customer_id: str

    billing_customer_id: str | None = None

    crm_account_status: (
        AccountStatus | None
    ) = None

    extracted_invoice_ids: list[str] = Field(
        default_factory=list,
    )

    invoice_statuses: dict[
        str,
        InvoiceStatus,
    ] = Field(
        default_factory=dict,
    )

    billing_hold_active: bool | None = None

    warnings: list[
        DataReadinessWarning
    ] = Field(
        default_factory=list,
    )


def extract_invoice_ids(
    description: str,
) -> list[str]:
    matches = (
        INVOICE_REFERENCE_PATTERN.findall(
            description
        )
    )

    invoice_ids: list[str] = []

    for match in matches:
        try:
            normalized = normalize_invoice_id(
                match
            )
        except LegacyBillingError:
            continue

        if normalized not in invoice_ids:
            invoice_ids.append(normalized)

    return invoice_ids


async def assess_data_readiness(
    *,
    case: CaseState,
    crm: CRMReader,
    billing: BillingReader,
) -> DataReadinessReport:
    warnings: list[
        DataReadinessWarning
    ] = []

    invoice_ids = extract_invoice_ids(
        case.description
    )

    if not invoice_ids:
        warnings.append(
            DataReadinessWarning(
                code=(
                    DataWarningCode
                    .NO_INVOICE_REFERENCE
                ),
                severity=(
                    DataWarningSeverity.INFO
                ),
                message=(
                    "No invoice reference was "
                    "detected in the case "
                    "description."
                ),
            )
        )

    try:
        customer = await crm.get_customer(
            case.customer_id
        )
    except IntegrationError as exc:
        warnings.append(
            DataReadinessWarning(
                code=(
                    DataWarningCode
                    .CRM_LOOKUP_FAILED
                ),
                severity=(
                    DataWarningSeverity.ERROR
                ),
                message=str(exc),
            )
        )

        return DataReadinessReport(
            customer_id=case.customer_id,
            extracted_invoice_ids=invoice_ids,
            warnings=warnings,
        )

    try:
        account = await crm.get_account(
            case.customer_id
        )
    except IntegrationError as exc:
        account = None

        warnings.append(
            DataReadinessWarning(
                code=(
                    DataWarningCode
                    .CRM_LOOKUP_FAILED
                ),
                severity=(
                    DataWarningSeverity.WARNING
                ),
                message=str(exc),
            )
        )

    billing_customer_id = (
        customer.billing_customer_id
    )

    if billing_customer_id is None:
        warnings.append(
            DataReadinessWarning(
                code=(
                    DataWarningCode
                    .MISSING_BILLING_ID
                ),
                severity=(
                    DataWarningSeverity.ERROR
                ),
                message=(
                    "CRM customer does not have "
                    "a billing customer ID."
                ),
            )
        )

        return DataReadinessReport(
            customer_id=case.customer_id,
            billing_customer_id=None,
            crm_account_status=(
                account.status
                if account is not None
                else None
            ),
            extracted_invoice_ids=invoice_ids,
            warnings=warnings,
        )

    invoice_statuses: dict[
        str,
        InvoiceStatus,
    ] = {}

    for invoice_id in invoice_ids[:3]:
        try:
            invoice = await billing.get_invoice(
                billing_customer_id,
                invoice_id,
            )

        except IntegrationError as exc:
            if exc.code == "CUST_MISMATCH":
                code = (
                    DataWarningCode
                    .CUSTOMER_INVOICE_MISMATCH
                )
            else:
                code = (
                    DataWarningCode
                    .INVOICE_LOOKUP_FAILED
                )

            warnings.append(
                DataReadinessWarning(
                    code=code,
                    severity=(
                        DataWarningSeverity.WARNING
                    ),
                    message=str(exc),
                )
            )

            continue

        invoice_statuses[
            invoice_id
        ] = invoice.status

        if (
            invoice.customer_id
            != billing_customer_id
        ):
            warnings.append(
                DataReadinessWarning(
                    code=(
                        DataWarningCode
                        .CUSTOMER_INVOICE_MISMATCH
                    ),
                    severity=(
                        DataWarningSeverity.ERROR
                    ),
                    message=(
                        f"Invoice {invoice_id} "
                        "belongs to a different "
                        "billing customer."
                    ),
                )
            )

    try:
        hold = (
            await billing
            .get_account_hold_optional(
                billing_customer_id
            )
        )
    except IntegrationError as exc:
        hold = None

        warnings.append(
            DataReadinessWarning(
                code=(
                    DataWarningCode
                    .BILLING_HOLD_LOOKUP_FAILED
                ),
                severity=(
                    DataWarningSeverity.WARNING
                ),
                message=str(exc),
            )
        )

    _append_status_warnings(
        account=account,
        hold=hold,
        warnings=warnings,
    )

    return DataReadinessReport(
        customer_id=case.customer_id,
        billing_customer_id=(
            billing_customer_id
        ),
        crm_account_status=(
            account.status
            if account is not None
            else None
        ),
        extracted_invoice_ids=invoice_ids,
        invoice_statuses=invoice_statuses,
        billing_hold_active=(
            hold.active
            if hold is not None
            else False
        ),
        warnings=warnings,
    )


def _append_status_warnings(
    *,
    account: Account | None,
    hold: AccountHold | None,
    warnings: list[
        DataReadinessWarning
    ],
) -> None:
    if account is None:
        return

    active_hold = (
        hold is not None
        and hold.active
    )

    if (
        account.status
        is AccountStatus.ACTIVE
        and active_hold
    ):
        warnings.append(
            DataReadinessWarning(
                code=(
                    DataWarningCode
                    .CRM_BILLING_STATUS_CONFLICT
                ),
                severity=(
                    DataWarningSeverity.WARNING
                ),
                message=(
                    "CRM reports ACTIVE while "
                    "Billing still has an active "
                    "account hold."
                ),
            )
        )

    if (
        account.status
        is AccountStatus.SUSPENDED
        and not active_hold
    ):
        warnings.append(
            DataReadinessWarning(
                code=(
                    DataWarningCode
                    .CRM_BILLING_STATUS_CONFLICT
                ),
                severity=(
                    DataWarningSeverity.WARNING
                ),
                message=(
                    "CRM reports SUSPENDED but "
                    "Billing has no active hold."
                ),
            )
        )