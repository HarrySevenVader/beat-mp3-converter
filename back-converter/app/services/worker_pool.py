from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock
from typing import Any, Callable

from app.core import get_settings


class ConversionWorkerPool:
    def __init__(self, max_workers: int | None = None) -> None:
        settings = get_settings()
        self.max_workers = max_workers or settings.worker_max_workers
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="conversion-worker")
        self._lock = Lock()

    def submit(self, task: Callable[..., Any], *args: object) -> Future[Any]:
        with self._lock:
            return self._executor.submit(task, *args)

    def shutdown(self) -> None:
        with self._lock:
            self._executor.shutdown(wait=False, cancel_futures=False)
