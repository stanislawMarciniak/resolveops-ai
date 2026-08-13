from pathlib import Path

from app.state import (
    CaseStage,
    CaseState,
    CaseStateRepository,
)
from app.state.database import (
    create_database_engine,
    create_session_factory,
    init_db,
)
from sqlalchemy import Engine


def make_repository(
    database_path: Path,
) -> tuple[Engine, CaseStateRepository]:
    engine = create_database_engine(
        f"sqlite:///{database_path}"
    )

    init_db(engine)

    session_factory = create_session_factory(
        engine,
    )

    repository = CaseStateRepository(
        session_factory,
    )

    return engine, repository


def test_repository_saves_and_loads_state(
    tmp_path: Path,
) -> None:
    engine, repository = make_repository(
        tmp_path / "state.db"
    )

    state = CaseState(
        customer_id="ACME",
        description=(
            "Account suspended despite invoice payment."
        ),
        stage=CaseStage.INVESTIGATING,
        model_calls=2,
        tool_calls=4,
    )

    persisted = repository.save(state)

    loaded = repository.require(
        state.case_id,
    )

    assert loaded == persisted
    assert loaded.stage is CaseStage.INVESTIGATING

    assert loaded.model_calls == 2
    assert loaded.tool_calls == 4

    engine.dispose()


def test_repository_updates_existing_state(
    tmp_path: Path,
) -> None:
    engine, repository = make_repository(
        tmp_path / "state.db"
    )

    state = repository.save(
        CaseState(
            customer_id="ACME",
            description=(
                "Account suspended despite "
                "invoice payment."
            ),
            stage=CaseStage.INVESTIGATING,
        )
    )

    updated = state.model_copy(
        update={
            "stage": CaseStage.PLANNING,
            "root_cause": (
                "Payment reference "
                "normalization mismatch."
            ),
            "model_calls": 3,
            "tool_calls": 5,
        }
    )

    persisted = repository.save(updated)

    loaded = repository.require(
        state.case_id,
    )

    assert loaded == persisted
    assert loaded.stage is CaseStage.PLANNING

    assert loaded.root_cause == (
        "Payment reference normalization mismatch."
    )

    engine.dispose()


def test_case_resumes_after_process_restart(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "state.db"

    # First backend process.
    first_engine, first_repository = (
        make_repository(database_path)
    )

    state = first_repository.save(
        CaseState(
            customer_id="ACME",
            description=(
                "Account suspended despite "
                "invoice payment."
            ),
            stage=CaseStage.PLANNING,
            root_cause=(
                "Payment reference "
                "normalization mismatch."
            ),
            model_calls=4,
            tool_calls=6,
        )
    )

    first_engine.dispose()

    # Simulated backend restart:
    # new engine + new repository.
    second_engine, second_repository = (
        make_repository(database_path)
    )

    resumed = second_repository.require(
        state.case_id,
    )

    assert resumed.stage is CaseStage.PLANNING

    assert resumed.root_cause == (
        "Payment reference normalization mismatch."
    )

    assert resumed.model_calls == 4
    assert resumed.tool_calls == 6

    second_engine.dispose()


def test_repository_returns_none_for_missing_case(
    tmp_path: Path,
) -> None:
    engine, repository = make_repository(
        tmp_path / "state.db"
    )

    result = repository.get(
        "00000000-0000-0000-0000-000000000000"
    )

    assert result is None

    engine.dispose()