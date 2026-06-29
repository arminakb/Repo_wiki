from __future__ import annotations

from pathlib import Path

from repo_wiki.config import Settings
from repo_wiki.core.extraction_service import ExtractionService
from repo_wiki.domain.enums import SourceType
from repo_wiki.domain.models import ExtractionResult
from repo_wiki.ingest.github import clone_github_repo, parse_github_url
from repo_wiki.ingest.local import resolve_local_repo
from repo_wiki.logging import log_event
from repo_wiki.storage.sqlite import SQLiteStore


class IngestionService:
    def __init__(self, settings: Settings, store: SQLiteStore):
        self.settings = settings
        self.store = store
        self.extractor = ExtractionService(settings)

    def ingest_local(
        self,
        path: str | Path,
        *,
        license_policy: str | None = None,
        include: list[str] | tuple[str, ...] | None = None,
        exclude: list[str] | tuple[str, ...] | None = None,
    ) -> ExtractionResult:
        root = resolve_local_repo(path)
        log_event("ingestion.started", source="local", path=str(root))
        result = self.extractor.extract_local(
            root,
            source_type=SourceType.LOCAL_REPO,
            visibility="local",
            license_policy=license_policy,
            include_patterns=tuple(include or ()),
            exclude_patterns=tuple(exclude or ()),
        )
        self.store.save_extraction(result)
        log_event(
            "ingestion.completed",
            repo_id=result.repository.id,
            files=len(result.files),
            knowledge_objects=len(result.knowledge_objects),
        )
        return result

    def ingest_github(
        self,
        url: str,
        *,
        branch: str | None = None,
        license_policy: str | None = None,
        include: list[str] | tuple[str, ...] | None = None,
        exclude: list[str] | tuple[str, ...] | None = None,
    ) -> ExtractionResult:
        owner, name = parse_github_url(url)
        log_event("ingestion.started", source="github", url=url, branch=branch)
        root = clone_github_repo(url, self.settings.clone_dir, branch)
        result = self.extractor.extract_local(
            root,
            source_type=SourceType.GITHUB_REPO,
            url=url,
            owner=owner,
            name=name,
            branch=branch,
            visibility="public",
            license_policy=license_policy,
            include_patterns=tuple(include or ()),
            exclude_patterns=tuple(exclude or ()),
        )
        self.store.save_extraction(result)
        log_event(
            "ingestion.completed",
            repo_id=result.repository.id,
            files=len(result.files),
            knowledge_objects=len(result.knowledge_objects),
        )
        return result
