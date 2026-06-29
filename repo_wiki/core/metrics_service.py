from __future__ import annotations

from repo_wiki.storage.sqlite import SQLiteStore


class MetricsService:
    def __init__(self, store: SQLiteStore):
        self.store = store

    def metrics(self) -> dict:
        return self.store.metrics()
