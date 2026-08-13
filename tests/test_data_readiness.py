from decimal import Decimal

import pytest
from app.agents.data_readiness import (
    DataWarningCode,
    assess_data_readiness,
    extract_invoice_ids,
)
from app.models import (
    Account,
    AccountHold,
    AccountStatus,
    Currency,
    Customer,
    Invoice,
    InvoiceStatus,
)
from app.state import CaseState


class FakeCRM:
    def __init__(
        self,
        *,
        customer: Customer,
        account: Account,
    ) -> None:
        self.customer = customer
        self.account = account

    async def get_customer(
        self,
        customer_id: str,
    ) -> Customer:
        return self.customer

    async def get_account(
        self,
        customer_id: str,
    ) -> Account:
        return self.account


class FakeBilling:
    def __init__(
        self,
        *,
        invoice: Invoice,
        hold: AccountHold | None,
    ) -> None:
        self.invoice = invoice
        self.hold = hold

    async def get_invoice(
        self,
        billing_customer_id: str,
        invoice_id: str,
    ) -> Invoice:
        return self.invoice

    async def get_account_hold_optional(
        self,
        billing_customer_id: str,
    ) -> AccountHold | None:
        return self.hold


def make_customer() -> Customer:
    return Customer(
        customer_id="ACME",
        name="ACME Corporation",
        billing_customer_id="000018392",
    )


def make_account(
    status: AccountStatus,
) -> Account:
    return Account(
        account_id="ACC-ACME",
        customer_id="ACME",
        status=status,
        plan="ENTERPRISE",
    )


def make_invoice() -> Invoice:
    return Invoice(
        invoice_id="INV-8231",
        customer_id="000018392",
        amount=Decimal("4999.00"),
        currency=Currency.PLN,
        status=InvoiceStatus.OVERDUE,
    )


def test_extract_invoice_ids() -> None:
    result = extract_invoice_ids(
        "Invoices INV8231, INV-8231 "
        "and INV 8231."
    )

    assert result == [
        "INV-8231",
    ]


@pytest.mark.asyncio
async def test_normal_acme_data() -> None:
    case = CaseState(
        customer_id="ACME",
        description=(
            "Account suspended after payment "
            "of INV-8231."
        ),
    )

    report = await assess_data_readiness(
        case=case,
        crm=FakeCRM(
            customer=make_customer(),
            account=make_account(
                AccountStatus.SUSPENDED
            ),
        ),
        billing=FakeBilling(
            invoice=make_invoice(),
            hold=AccountHold(
                customer_id="000018392",
                hold_code="PAYMENT_OVERDUE",
                active=True,
            ),
        ),
    )

    assert (
        report.extracted_invoice_ids
        == ["INV-8231"]
    )

    assert (
        report.invoice_statuses[
            "INV-8231"
        ]
        is InvoiceStatus.OVERDUE
    )

    assert report.warnings == []


@pytest.mark.asyncio
async def test_suspended_without_hold_warns() -> None:
    case = CaseState(
        customer_id="ACME",
        description="Invoice INV-8231.",
    )

    report = await assess_data_readiness(
        case=case,
        crm=FakeCRM(
            customer=make_customer(),
            account=make_account(
                AccountStatus.SUSPENDED
            ),
        ),
        billing=FakeBilling(
            invoice=make_invoice(),
            hold=None,
        ),
    )

    codes = {
        warning.code
        for warning in report.warnings
    }

    assert (
        DataWarningCode
        .CRM_BILLING_STATUS_CONFLICT
        in codes
    )


@pytest.mark.asyncio
async def test_missing_billing_id_warns() -> None:
    customer = Customer(
        customer_id="ACME",
        name="ACME Corporation",
        billing_customer_id=None,
    )

    case = CaseState(
        customer_id="ACME",
        description="Invoice INV-8231.",
    )

    report = await assess_data_readiness(
        case=case,
        crm=FakeCRM(
            customer=customer,
            account=make_account(
                AccountStatus.SUSPENDED
            ),
        ),
        billing=FakeBilling(
            invoice=make_invoice(),
            hold=None,
        ),
    )

    codes = {
        warning.code
        for warning in report.warnings
    }

    assert (
        DataWarningCode.MISSING_BILLING_ID
        in codes
    )