from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock


class MetricsService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._started_at = datetime.now(timezone.utc)
        self._counters: dict[str, int] = {
            "http_requests_total": 0,
            "http_4xx_total": 0,
            "http_5xx_total": 0,
            "conversion_jobs_created_total": 0,
            "conversion_jobs_completed_total": 0,
            "conversion_jobs_failed_total": 0,
            "conversion_downloads_total": 0,
            "conversion_active_jobs": 0,
        }

    def record_http_status(self, status_code: int) -> None:
        with self._lock:
            self._counters["http_requests_total"] += 1
            if 400 <= status_code < 500:
                self._counters["http_4xx_total"] += 1
            if status_code >= 500:
                self._counters["http_5xx_total"] += 1

    def record_job_created(self) -> None:
        with self._lock:
            self._counters["conversion_jobs_created_total"] += 1
            self._counters["conversion_active_jobs"] += 1

    def record_job_completed(self) -> None:
        with self._lock:
            self._counters["conversion_jobs_completed_total"] += 1
            if self._counters["conversion_active_jobs"] > 0:
                self._counters["conversion_active_jobs"] -= 1

    def record_job_failed(self) -> None:
        with self._lock:
            self._counters["conversion_jobs_failed_total"] += 1
            if self._counters["conversion_active_jobs"] > 0:
                self._counters["conversion_active_jobs"] -= 1

    def record_download(self) -> None:
        with self._lock:
            self._counters["conversion_downloads_total"] += 1

    def snapshot(self) -> dict[str, object]:
        now = datetime.now(timezone.utc)
        with self._lock:
            counters = dict(self._counters)
            started_at = self._started_at

        uptime_seconds = int((now - started_at).total_seconds())
        return {
            "started_at": started_at.isoformat(),
            "uptime_seconds": uptime_seconds,
            "counters": counters,
        }


metrics_service = MetricsService()
