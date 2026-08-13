from app.mcp.metadata import (
    ToolAccess,
    get_tool_definition,
)


def test_get_invoice_is_read_only() -> None:
    tool = get_tool_definition(
        "get_invoice"
    )

    assert tool.access is ToolAccess.READ

    assert not tool.requires_approval


def test_match_payment_requires_approval() -> None:
    tool = get_tool_definition(
        "match_payment"
    )

    assert tool.access is ToolAccess.WRITE

    assert tool.requires_approval


def test_remove_hold_requires_approval() -> None:
    tool = get_tool_definition(
        "remove_account_hold"
    )

    assert tool.access is ToolAccess.WRITE

    assert tool.requires_approval

def test_search_policies_is_read_only() -> None:
    tool = get_tool_definition(
        "search_policies"
    )

    assert tool.access is ToolAccess.READ
    assert not tool.requires_approval