"""
AgriNova Backend — SQLAlchemy engine, session factory, declarative base.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.db import models  # noqa: F401  (ensure models are registered)
    Base.metadata.create_all(bind=engine)
    _migrate_additive_columns()


def _migrate_additive_columns():
    """create_all() only creates missing tables — it never ALTERs existing
    ones. New nullable/defaulted columns on tables that already exist in a
    deployed DB must be patched in by hand here, guarded so re-running is a
    no-op."""
    with engine.connect() as conn:
        cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(farms)")}
        if "sensor_mode" not in cols:
            conn.exec_driver_sql("ALTER TABLE farms ADD COLUMN sensor_mode VARCHAR(16) DEFAULT 'Auto'")
            conn.commit()
        if "hardware_enabled" not in cols:
            conn.exec_driver_sql("ALTER TABLE farms ADD COLUMN hardware_enabled BOOLEAN DEFAULT 0")
            conn.exec_driver_sql("ALTER TABLE farms ADD COLUMN sensor_node_host VARCHAR(128) DEFAULT ''")
            conn.exec_driver_sql("ALTER TABLE farms ADD COLUMN robot_host VARCHAR(128) DEFAULT ''")
            conn.exec_driver_sql("ALTER TABLE farms ADD COLUMN camera_host VARCHAR(128) DEFAULT ''")
            conn.commit()
