"""Database session and engine management utilities."""

from __future__ import annotations

import threading
from typing import Iterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()

_SessionFactory = sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False
)
_engine_lock = threading.Lock()
_engine: Optional[Engine] = None
_engine_url: Optional[str] = None
_schema_initialized = False


def _build_engine(database_url: str) -> Engine:
    kwargs: dict[str, object] = {"future": True}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if database_url.endswith(":memory:"):
            kwargs["poolclass"] = StaticPool
    return create_engine(database_url, **kwargs)


def configure_engine(database_url: str) -> Engine:
    """Create or reuse an engine bound to ``database_url``."""

    global _engine, _engine_url
    with _engine_lock:
        if _engine is None or _engine_url != database_url:
            _engine = _build_engine(database_url)
            _engine_url = database_url
            _SessionFactory.configure(bind=_engine)
            _initialize_schema(_engine)
    return _engine  # type: ignore[return-value]


def get_engine(database_url: Optional[str] = None) -> Engine:
    """Return the active engine, configuring it first if required."""

    global _engine
    if _engine is None:
        if not database_url:
            raise RuntimeError("Database engine not configured. Provide database_url.")
        return configure_engine(database_url)
    if database_url and database_url != _engine_url:
        return configure_engine(database_url)
    return _engine


def _initialize_schema(engine: Engine) -> None:
    global _schema_initialized
    if _schema_initialized:
        return
    if engine.url.get_backend_name() == "sqlite":
        Base.metadata.create_all(bind=engine)
    _schema_initialized = True


def get_db_session(database_url: Optional[str] = None) -> Iterator[Session]:
    """Yield a transactional SQLAlchemy session."""

    get_engine(database_url)
    session: Session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine() -> None:
    """Reset the engine/session state (primarily for testing)."""

    global _engine, _engine_url, _schema_initialized
    with _engine_lock:
        _engine = None
        _engine_url = None
        _schema_initialized = False
        _SessionFactory.configure(bind=None)
