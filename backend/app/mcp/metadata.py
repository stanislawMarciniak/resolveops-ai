from enum import StrEnum

from app.models.base import DomainModel
from app.models.enums import RiskLevel
from mcp.types import ToolAnnotations
from pydantic import Field


class ToolAccess(StrEnum):
    READ = "READ"
    WRITE = "WRITE"


class ToolDefinition(DomainModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str = Field(
        min_length=1,
        max_length=500,
    )

    access: ToolAccess
    risk: RiskLevel

    requires_approval: bool

    destructive: bool = False
    idempotent: bool = False
    open_world: bool = False


TOOL_REGISTRY: dict[str, ToolDefinition] = {
    "get_customer": ToolDefinition(
        name="get_customer",
        title="Get customer",
        description=(
            "Read canonical customer information "
            "from the CRM."
        ),
        access=ToolAccess.READ,
        risk=RiskLevel.LOW,
        requires_approval=False,
    ),
    "get_account": ToolDefinition(
        name="get_account",
        title="Get customer account",
        description=(
            "Read the current customer account "
            "state from the CRM."
        ),
        access=ToolAccess.READ,
        risk=RiskLevel.LOW,
        requires_approval=False,
    ),
    "get_invoice": ToolDefinition(
        name="get_invoice",
        title="Get invoice",
        description=(
            "Read a normalized invoice together "
            "with its original legacy billing "
            "identifier for diagnostic comparison."
        ),
        access=ToolAccess.READ,
        risk=RiskLevel.LOW,
        requires_approval=False,
    ),
    "search_payments": ToolDefinition(
        name="search_payments",
        title="Search customer payments",
        description=(
            "Read normalized customer payments "
            "together with their original legacy "
            "invoice references."
        ),
        access=ToolAccess.READ,
        risk=RiskLevel.LOW,
        requires_approval=False,
    ),
    "get_account_hold": ToolDefinition(
        name="get_account_hold",
        title="Get account hold",
        description=(
            "Read the current billing hold "
            "for a customer."
        ),
        access=ToolAccess.READ,
        risk=RiskLevel.LOW,
        requires_approval=False,
    ),
    "search_policies": ToolDefinition(
        name="search_policies",
        title="Search policies",
        description=(
            "Search internal policies, "
            "runbooks, SLAs, and "
            "customer-specific contracts."
        ),
        access=ToolAccess.READ,
        risk=RiskLevel.LOW,
        requires_approval=False,
    ),
    "match_payment": ToolDefinition(
        name="match_payment",
        title="Match payment to invoice",
        description=(
            "Associate a received payment with "
            "an existing invoice."
        ),
        access=ToolAccess.WRITE,
        risk=RiskLevel.MEDIUM,
        requires_approval=True,
        destructive=False,
        idempotent=True,
    ),
    "remove_account_hold": ToolDefinition(
        name="remove_account_hold",
        title="Remove account hold",
        description=(
            "Remove an active billing hold "
            "from a customer account."
        ),
        access=ToolAccess.WRITE,
        risk=RiskLevel.MEDIUM,
        requires_approval=True,
        destructive=False,
        idempotent=True,
    ),
}


def get_tool_definition(
    name: str,
) -> ToolDefinition:
    try:
        return TOOL_REGISTRY[name]
    except KeyError as exc:
        raise KeyError(
            f"Unknown tool: {name}"
        ) from exc


def to_mcp_annotations(
    definition: ToolDefinition,
) -> ToolAnnotations:
    if definition.access is ToolAccess.READ:
        return ToolAnnotations(
            readOnlyHint=True,
            openWorldHint=definition.open_world,
        )

    return ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=definition.destructive,
        idempotentHint=definition.idempotent,
        openWorldHint=definition.open_world,
    )