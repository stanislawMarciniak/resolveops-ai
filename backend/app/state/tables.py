from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.state.database import Base


class CaseStateRecord(Base):
    __tablename__ = "case_states"

    case_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    customer_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    stage: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )