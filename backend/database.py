import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, MetaData, Table, func

DATABASE_URL = os.getenv(
    "DB_URL", "postgresql://zabbix:zabbix@timescaledb:5432/metrics"
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

# SQLAlchemy metadata
metadata = MetaData()

# Metrics table definition (suitable for TimescaleDB hypertable)
metrics_table = Table(
    "metrics",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("host_id", String, nullable=False, index=True),
    Column("item_key", String, nullable=False),
    Column("value", Float, nullable=False),
    Column("timestamp", DateTime(timezone=True), server_default=func.now(), index=True),
)

# Email config (single-row)
email_config_table = Table(
    "email_config",
    metadata,
    Column("id", Integer, primary_key=True),  # always 1
    Column("smtp_host", String, nullable=True),
    Column("smtp_port", Integer, nullable=True),
    Column("smtp_user", String, nullable=True),
    Column("smtp_password", String, nullable=True),
    Column("recipients", String, nullable=True),
)

anomalies_table = Table(
    "anomalies",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("host_id", String, nullable=False, index=True),
    Column("item_key", String, nullable=False),
    Column("value", Float, nullable=False),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("reason", String, nullable=True),  # e.g., '3-sigma rule'
)


import time
from sqlalchemy.exc import OperationalError


def init_db(max_retries: int = 10, delay: int = 3):
    """Attempt to create tables, retrying until TimescaleDB is ready.

    Parameters
    ----------
    max_retries: Number of attempts before giving up.
    delay: Seconds to wait between retries.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            metadata.create_all(engine)
            return  # success
        except OperationalError as exc:  # DB not ready yet
            attempt += 1
            print(f"[DB] cannot connect yet ({exc}); retry {attempt}/{max_retries}...")
            time.sleep(delay)
    raise RuntimeError("TimescaleDB is still unreachable after retries")
