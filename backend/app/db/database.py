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
        user_cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)")}
        if "failed_login_attempts" not in user_cols:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0")
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN locked_until DATETIME DEFAULT NULL")
            conn.commit()

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

        state_cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(farm_state)")}
        if "motor_speed" not in state_cols:
            conn.exec_driver_sql("ALTER TABLE farm_state ADD COLUMN motor_speed INTEGER DEFAULT 100")
            conn.commit()
        if "lid_open" in state_cols:
            # Column removed from the ORM model when the rainwater-harvesting
            # feature was dropped. SQLite still enforces its NOT NULL
            # constraint on any DB file created before that change, and since
            # the ORM no longer supplies a value for it, every farm_state
            # insert (i.e. every new farm/onboarding) fails. Requires SQLite
            # 3.35+ for DROP COLUMN (bundled Python ships 3.45+).
            conn.exec_driver_sql("ALTER TABLE farm_state DROP COLUMN lid_open")
            conn.commit()
