from __future__ import annotations

from repo_wiki.config import Settings
from repo_wiki.core.ingestion_service import IngestionService
from repo_wiki.core.retrieval_service import RetrievalService
from repo_wiki.discovery.github_client import discover_repositories
from repo_wiki.retrieval.classifier import infer_framework
from repo_wiki.storage.sqlite import SQLiteStore


class LiveResearchEngine:
    def __init__(self, settings: Settings, store: SQLiteStore):
        self.settings = settings
        self.store = store

    def search(self, query: str, *, limit: int = 5, max_tokens: int = 4000) -> dict:
        topic = infer_framework(query) or query
        repos = discover_repositories(topic, min_stars=500, limit=1)
        if not repos:
            raise RuntimeError(f"live research found no repositories for: {topic}")

        # ponytail: live fallback indexes one repo; add staging/docs fetch when quality needs it.
        IngestionService(self.settings, self.store).ingest_github(repos[0].url)
        return RetrievalService(self.store).retrieve(query, limit=limit, max_tokens=max_tokens)
