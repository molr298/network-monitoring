"""Background thread that periodically analyzes metrics to find anomalies."""

import threading
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_, func, insert

from database import engine, metrics_table, anomalies_table

DETECT_INTERVAL = 300  # seconds

class AnomalyDetector(threading.Thread):
    """Periodically analyze metrics to find anomalies."""

    def __init__(self):
        super().__init__(daemon=True)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        print("[AnomalyDetector] Starting up...")
        while not self._stop_event.is_set():
            try:
                self.detect_anomalies_once()
            except Exception as exc:
                print(f"[AnomalyDetector] error: {exc}")
            finally:
                self._stop_event.wait(DETECT_INTERVAL)

    def detect_anomalies_once(self):
        """Check for anomalies in the last hour of metric data."""
        with engine.begin() as conn:
            # Get all distinct host/item pairs
            metric_pairs_stmt = select(metrics_table.c.host_id, metrics_table.c.item_key).distinct()
            metric_pairs = conn.execute(metric_pairs_stmt).fetchall()

            since = datetime.now(timezone.utc) - timedelta(hours=1)

            for host_id, item_key in metric_pairs:
                # For each pair, get stats for the last hour
                stats_stmt = select(
                    func.avg(metrics_table.c.value).label("mean"),
                    func.stddev(metrics_table.c.value).label("stddev")
                ).where(
                    and_(
                        metrics_table.c.host_id == host_id,
                        metrics_table.c.item_key == item_key,
                        metrics_table.c.timestamp >= since
                    )
                )
                stats = conn.execute(stats_stmt).first()

                if stats and stats.mean is not None and stats.stddev is not None:
                    mean = stats.mean
                    stddev = stats.stddev
                    # 3-sigma rule
                    upper_bound = mean + (3 * stddev)
                    lower_bound = mean - (3 * stddev)

                    # Find the latest metric value to check against the bounds
                    latest_metric_stmt = select(metrics_table.c.value, metrics_table.c.timestamp)\
                        .where(
                            and_(
                                metrics_table.c.host_id == host_id,
                                metrics_table.c.item_key == item_key
                            )
                        ).order_by(metrics_table.c.timestamp.desc()).limit(1)
                    
                    latest_metric = conn.execute(latest_metric_stmt).first()

                    if latest_metric and (latest_metric.value > upper_bound or latest_metric.value < lower_bound):
                        # Check if this anomaly was already reported recently
                        recent_anomaly_stmt = select(anomalies_table).where(
                            and_(
                                anomalies_table.c.host_id == host_id,
                                anomalies_table.c.item_key == item_key,
                                anomalies_table.c.timestamp >= since
                            )
                        ).limit(1)
                        
                        if conn.execute(recent_anomaly_stmt).first():
                            continue # Already reported

                        # Insert new anomaly
                        conn.execute(
                            insert(anomalies_table),
                            [{
                                "host_id": host_id,
                                "item_key": item_key,
                                "value": latest_metric.value,
                                "timestamp": latest_metric.timestamp,
                                "reason": f"3-sigma rule (mean={mean:.2f}, stddev={stddev:.2f})"
                            }]
                        )
                        print(f"[AnomalyDetector] New anomaly detected for {host_id}/{item_key}: value {latest_metric.value:.2f}")
