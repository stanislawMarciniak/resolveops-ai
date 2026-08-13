from typing import Any

import pytest
from app.agents.investigator import (
    InvestigationOutcome,
    InvestigationResult,
    InvestigatorToolGuardrail,
)
from pydantic import ValidationError


class FakeTool:
    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name


class FakeToolContext:
    def __init__(self) -> None:
        self.state: dict[str, Any] = {}


def test_root_cause_required() -> None:
    with pytest.raises(
        ValidationError
    ):
        InvestigationResult(
            outcome=(
                InvestigationOutcome
                .ROOT_CAUSE_FOUND
            ),
            evidence=[],
            hypotheses=[],
            root_cause=None,
            root_cause_confidence=0.9,
            summary="Cause found.",
        )


def test_write_tool_is_blocked() -> None:
    guardrail = (
        InvestigatorToolGuardrail(
            max_tool_calls=8
        )
    )

    context = FakeToolContext()

    result = guardrail(
        FakeTool("match_payment"),  # type: ignore[arg-type]
        {
            "payment_id": "TX-9912",
            "invoice_id": "INV-8231",
        },
        context,  # type: ignore[arg-type]
    )

    assert result is not None

    assert (
        result["error"]
        == "TOOL_NOT_ALLOWED"
    )


def test_repeated_tool_loop_is_blocked() -> None:
    guardrail = (
        InvestigatorToolGuardrail(
            max_tool_calls=8
        )
    )

    context = FakeToolContext()

    tool = FakeTool(
        "get_invoice"
    )

    args = {
        "customer_id": "ACME",
        "invoice_id": "INV-8231",
    }

    first = guardrail(
        tool,  # type: ignore[arg-type]
        args,
        context,  # type: ignore[arg-type]
    )

    second = guardrail(
        tool,  # type: ignore[arg-type]
        args,
        context,  # type: ignore[arg-type]
    )

    third = guardrail(
        tool,  # type: ignore[arg-type]
        args,
        context,  # type: ignore[arg-type]
    )

    assert first is None
    assert second is None

    assert third is not None

    assert (
        third["error"]
        == "REPEATED_TOOL_CALL_BLOCKED"
    )

    assert (
        context.state[
            "investigator_tool_calls"
        ]
        == 2
    )


def test_tool_call_limit() -> None:
    guardrail = (
        InvestigatorToolGuardrail(
            max_tool_calls=2
        )
    )

    context = FakeToolContext()

    assert (
        guardrail(
            FakeTool("get_customer"),  # type: ignore[arg-type]
            {"customer_id": "ACME"},
            context,  # type: ignore[arg-type]
        )
        is None
    )

    assert (
        guardrail(
            FakeTool("get_account"),  # type: ignore[arg-type]
            {"customer_id": "ACME"},
            context,  # type: ignore[arg-type]
        )
        is None
    )

    result = guardrail(
        FakeTool("search_payments"),  # type: ignore[arg-type]
        {"customer_id": "ACME"},
        context,  # type: ignore[arg-type]
    )

    assert result is not None

    assert (
        result["error"]
        == "TOOL_CALL_LIMIT_REACHED"
    )