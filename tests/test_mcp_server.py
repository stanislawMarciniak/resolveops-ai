import pytest
from app.mcp.server import mcp


@pytest.mark.asyncio
async def test_mcp_exposes_expected_tools() -> None:
    tools = await mcp.list_tools()

    names = {
        tool.name
        for tool in tools
    }

    assert names == {
        "get_customer",
        "get_account",
        "get_invoice",
        "search_payments",
        "get_account_hold",
        "search_policies",
        "match_payment",
        "remove_account_hold",
    }


@pytest.mark.asyncio
async def test_read_and_write_annotations() -> None:
    tools = {
        tool.name: tool
        for tool in await mcp.list_tools()
    }

    get_invoice = tools["get_invoice"]

    assert get_invoice.annotations is not None
    assert get_invoice.annotations.readOnlyHint is True

    match_payment = tools["match_payment"]

    assert match_payment.annotations is not None
    assert match_payment.annotations.readOnlyHint is False