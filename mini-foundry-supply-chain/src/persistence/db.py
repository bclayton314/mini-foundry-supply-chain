from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


DATABASE_PATH = Path("data/mini_foundry.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

Base = declarative_base()

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


def init_db() -> None:
    """
    Create database tables if they do not already exist.
    """
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Import models here so SQLAlchemy registers them before create_all().
    from persistence import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """
    Create a new database session.
    """
    return SessionLocal()