from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def create_database_engine(
    database_url: str,
) -> Engine:
    connect_args: dict[str, bool] = {}

    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )


def create_session_factory(
    engine: Engine,
) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


settings = get_settings()

engine = create_database_engine(
    settings.database_url,
)

SessionLocal = create_session_factory(engine)


def init_db(
    target_engine: Engine = engine,
) -> None:
    # Import registers ORM tables on Base.metadata.
    from app.state import tables  # noqa: F401

    Base.metadata.create_all(
        bind=target_engine,
    )