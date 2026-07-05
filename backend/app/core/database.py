"""SQLAlchemy engine and session setup. Migrations come in Step 4."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def check_database_connection() -> None:
    """Verify Postgres is reachable. Called on startup when DB check is enabled."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
