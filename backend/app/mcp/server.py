from functools import lru_cache
from typing import Annotated

from app.config import get_settings
from app.integrations.billing.client import (
    BillingClient,
)
from app.integrations.billing.results import (
    InvoiceLookupResult,
    PaymentLookupResult,
)
from app.integrations.crm.client import CRMClient
from app.integrations.errors import IntegrationError
from app.mcp.metadata import (
    get_tool_definition,
    to_mcp_annotations,
)
from app.mcp.schemas import OperationResult
from app.models import (
    Account,
    AccountHold,
    Customer,
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
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import (
    TransportSecuritySettings,
)
from pydantic import Field
from starlette.requests import Request
from starlette.responses import (
    JSONResponse,
    Response,
)

settings = get_settings()


crm_client = CRMClient(
    base_url=settings.crm_base_url,
)

billing_client = BillingClient(
    base_url=settings.billing_base_url,
)

transport_security = TransportSecuritySettings(
    allowed_hosts=[
        "localhost:*",
        "127.0.0.1:*",
        "mcp:*",
    ],
    allowed_origins=[],
)

mcp = FastMCP(
    "ResolveOps Enterprise Tools",
    host=settings.mcp_host,
    port=settings.mcp_port,
    transport_security=transport_security,
)


async def get_billing_customer_id(
    customer_id: str,
) -> str:
    customer = await crm_client.get_customer(
        customer_id
    )

    if customer.billing_customer_id is None:
        raise IntegrationError(
            f"Customer {customer_id!r} "
            "does not have a billing customer ID."
        )

    return customer.billing_customer_id


GET_CUSTOMER = get_tool_definition(
    "get_customer"
)


@mcp.tool(
    title=GET_CUSTOMER.title,
    annotations=to_mcp_annotations(
        GET_CUSTOMER
    ),
)
async def get_customer(
    customer_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            description=(
                "Canonical CRM customer ID, "
                "for example ACME."
            ),
        ),
    ],
) -> Customer:
    """Get canonical customer information from CRM."""

    return await crm_client.get_customer(
        customer_id
    )


GET_ACCOUNT = get_tool_definition(
    "get_account"
)


@mcp.tool(
    title=GET_ACCOUNT.title,
    annotations=to_mcp_annotations(
        GET_ACCOUNT
    ),
)
async def get_account(
    customer_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            description=(
                "Canonical CRM customer ID."
            ),
        ),
    ],
) -> Account:
    """Get the current CRM account for a customer."""

    return await crm_client.get_account(
        customer_id
    )


GET_INVOICE = get_tool_definition(
    "get_invoice"
)


@mcp.tool(
    title=GET_INVOICE.title,
    annotations=to_mcp_annotations(
        GET_INVOICE
    ),
)
async def get_invoice(
    customer_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            description=(
                "Canonical CRM customer ID."
            ),
        ),
    ],
    invoice_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            description=(
                "Canonical invoice ID, "
                "for example INV-8231."
            ),
        ),
    ],
) -> InvoiceLookupResult:
    """
    Get an invoice together with the original
    identifier used by legacy Billing.
    """

    billing_customer_id = (
        await get_billing_customer_id(
            customer_id
        )
    )

    return (
        await billing_client
        .get_invoice_with_provenance(
            billing_customer_id,
            invoice_id,
        )
    )


SEARCH_PAYMENTS = get_tool_definition(
    "search_payments"
)


@mcp.tool(
    title=SEARCH_PAYMENTS.title,
    annotations=to_mcp_annotations(
        SEARCH_PAYMENTS
    ),
)
async def search_payments(
    customer_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            description=(
                "Canonical CRM customer ID."
            ),
        ),
    ],
) -> list[PaymentLookupResult]:
    """
    Search customer payments together with
    their original legacy invoice references.
    """

    billing_customer_id = (
        await get_billing_customer_id(
            customer_id
        )
    )

    return (
        await billing_client
        .search_payments_with_provenance(
            billing_customer_id
        )
    )


GET_ACCOUNT_HOLD = get_tool_definition(
    "get_account_hold"
)


@mcp.tool(
    title=GET_ACCOUNT_HOLD.title,
    annotations=to_mcp_annotations(
        GET_ACCOUNT_HOLD
    ),
)
async def get_account_hold(
    customer_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            description=(
                "Canonical CRM customer ID."
            ),
        ),
    ],
) -> AccountHold:
    """Get the current billing hold for a customer."""

    billing_customer_id = (
        await get_billing_customer_id(
            customer_id
        )
    )

    return await billing_client.get_account_hold(
        billing_customer_id
    )


MATCH_PAYMENT = get_tool_definition(
    "match_payment"
)


@mcp.tool(
    title=MATCH_PAYMENT.title,
    annotations=to_mcp_annotations(
        MATCH_PAYMENT
    ),
)
async def match_payment(
    customer_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            description=(
                "Canonical CRM customer ID."
            ),
        ),
    ],
    payment_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            description="Payment ID.",
        ),
    ],
    invoice_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            description=(
                "Canonical invoice ID."
            ),
        ),
    ],
) -> OperationResult:
    """Match a received payment to an invoice."""

    billing_customer_id = (
        await get_billing_customer_id(
            customer_id
        )
    )

    # Preflight validation ensures that the invoice
    # actually belongs to the requested customer.
    await billing_client.get_invoice(
        billing_customer_id,
        invoice_id,
    )

    await billing_client.match_payment(
        payment_id,
        invoice_id,
    )

    return OperationResult(
        success=True,
        operation="match_payment",
        message=(
            f"Payment {payment_id} was matched "
            f"to {invoice_id}."
        ),
    )


REMOVE_ACCOUNT_HOLD = get_tool_definition(
    "remove_account_hold"
)


@mcp.tool(
    title=REMOVE_ACCOUNT_HOLD.title,
    annotations=to_mcp_annotations(
        REMOVE_ACCOUNT_HOLD
    ),
)
async def remove_account_hold(
    customer_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            description=(
                "Canonical CRM customer ID."
            ),
        ),
    ],
) -> OperationResult:
    """Remove an active billing hold for a customer."""

    billing_customer_id = (
        await get_billing_customer_id(
            customer_id
        )
    )

    await billing_client.remove_account_hold(
        billing_customer_id
    )

    account = await crm_client.restore_account(
        customer_id
    )

    return OperationResult(
        success=True,
        operation="remove_account_hold",
        message=(
            "Billing hold removed and CRM "
            f"account {account.account_id} "
            "restored to ACTIVE."
        ),
    )

@lru_cache
def get_policy_retriever() -> PolicyRetriever:
    embeddings = GeminiEmbeddingProvider(
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        api_key=settings.google_api_key,
    )

    return PolicyRetriever(
        index_path=(
            settings.policy_index_path
        ),
        embeddings=embeddings,
        top_k=(
            settings.policy_search_top_k
        ),
    )

SEARCH_POLICIES = get_tool_definition(
    "search_policies"
)


@mcp.tool(
    title=SEARCH_POLICIES.title,
    annotations=to_mcp_annotations(
        SEARCH_POLICIES
    ),
)
async def search_policies(
    query: Annotated[
        str,
        Field(
            min_length=3,
            max_length=500,
            description=(
                "Question or topic to search "
                "for in internal policies."
            ),
        ),
    ],
    customer_id: Annotated[
        str | None,
        Field(
            max_length=64,
            description=(
                "Canonical customer ID when "
                "customer-specific contracts "
                "should be included."
            ),
        ),
    ] = None,
) -> list[PolicySearchResult]:
    """Search internal policy and runbook knowledge."""

    retriever = get_policy_retriever()

    return await retriever.search(
        query=query,
        customer_id=customer_id,
    )

@mcp.custom_route( # type: ignore[untyped-decorator]
    "/health",
    methods=["GET"],
)
async def health(
    _: Request,
) -> Response:
    return JSONResponse(
        {
            "status": "ok",
            "service": "resolveops-mcp",
        }
    )


transport_security = (
    TransportSecuritySettings(
        allowed_hosts=[
            "localhost:*",
            "127.0.0.1:*",
            "mcp:*",
        ],
        allowed_origins=[],
    )
)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
    )