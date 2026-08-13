from app.state import (
    CaseStage,
    CaseState,
)


def test_case_state_has_safe_defaults() -> None:
    state = CaseState(
        customer_id="ACME",
        description=(
            "Account suspended despite invoice payment."
        ),
    )

    assert state.stage is CaseStage.NEW

    assert state.evidence == []
    assert state.hypotheses == []
    assert state.executed_actions == []

    assert state.root_cause is None
    assert state.resolution_plan is None
    assert state.review is None

    assert (
        state.plan_revision_count
        == 0
    )
    assert state.approval is None
    assert state.verification is None

    assert state.model_calls == 0
    assert state.tool_calls == 0

    assert state.input_tokens == 0
    assert state.output_tokens == 0

    assert state.estimated_cost_usd == 0.0

    assert not state.is_terminal


def test_terminal_stage_is_detected() -> None:
    state = CaseState(
        customer_id="ACME",
        description="Resolved case.",
        stage=CaseStage.RESOLVED,
    )

    assert state.is_terminal


def test_case_state_round_trip() -> None:
    state = CaseState(
        customer_id="ACME",
        description=(
            "Account suspended despite invoice payment."
        ),
        stage=CaseStage.INVESTIGATING,
        model_calls=2,
        tool_calls=3,
        input_tokens=900,
        output_tokens=120,
        estimated_cost_usd=0.0042,
    )

    payload = state.model_dump(
        mode="json",
    )

    restored = CaseState.model_validate(
        payload,
    )

    assert restored == state