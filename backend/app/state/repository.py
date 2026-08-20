from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from app.state.case_state import CaseState
from app.state.tables import CaseStateRecord


def utc_now() -> datetime:
    return datetime.now(UTC)


class CaseStateRepository:
    """Persistence boundary for workflow state."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def save(
        self,
        state: CaseState,
    ) -> CaseState:
        persisted_state = state.model_copy(
            update={
                "updated_at": utc_now(),
            }
        )

        payload = persisted_state.model_dump(
            mode="json",
        )

        case_id = str(
            persisted_state.case_id,
        )

        with self._session_factory() as session:
            record = session.get(
                CaseStateRecord,
                case_id,
            )

            if record is None:
                record = CaseStateRecord(
                    case_id=case_id,
                    customer_id=persisted_state.customer_id,
                    stage=persisted_state.stage.value,
                    payload=payload,
                    created_at=persisted_state.created_at,
                    updated_at=persisted_state.updated_at,
                )

                session.add(record)

            else:
                record.customer_id = (
                    persisted_state.customer_id
                )

                record.stage = (
                    persisted_state.stage.value
                )

                record.payload = payload

                record.updated_at = (
                    persisted_state.updated_at
                )

            session.commit()

        return persisted_state

    def get(
        self,
        case_id: UUID | str,
    ) -> CaseState | None:
        with self._session_factory() as session:
            record = session.get(
                CaseStateRecord,
                str(case_id),
            )

            if record is None:
                return None

            return CaseState.model_validate(
                record.payload,
            )

    def require(
        self,
        case_id: UUID | str,
    ) -> CaseState:
        state = self.get(case_id)

        if state is None:
            raise LookupError(
                f"Case {case_id} was not found."
            )

        return state

    def list(
        self,
        *,
        customer_id: str | None = None,
        stage: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CaseState]:
        with self._session_factory() as session:
            query = session.query(CaseStateRecord)

            if customer_id is not None:
                query = query.filter(
                    CaseStateRecord.customer_id
                    == customer_id
                )

            if stage is not None:
                query = query.filter(
                    CaseStateRecord.stage == stage
                )

            records = (
                query.order_by(
                    CaseStateRecord.updated_at.desc()
                )
                .offset(max(offset, 0))
                .limit(max(min(limit, 500), 1))
                .all()
            )

            return [
                CaseState.model_validate(
                    record.payload
                )
                for record in records
            ]

    def count(
        self,
        *,
        customer_id: str | None = None,
        stage: str | None = None,
    ) -> int:
        with self._session_factory() as session:
            query = session.query(CaseStateRecord)

            if customer_id is not None:
                query = query.filter(
                    CaseStateRecord.customer_id
                    == customer_id
                )

            if stage is not None:
                query = query.filter(
                    CaseStateRecord.stage == stage
                )

            return query.count()