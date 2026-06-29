from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from repo_wiki.domain.enums import FeedbackStatus, KnowledgeType, SourceType


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class RepoWikiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class Repository(RepoWikiModel):
    id: str
    source_type: SourceType
    owner: str | None = None
    name: str
    url: str | None = None
    local_path: str | None = None
    default_branch: str | None = None
    visibility: str = "local"
    license: str | None = None
    primary_language: str | None = None
    detected_languages: dict[str, float] = Field(default_factory=dict)
    detected_frameworks: list[str] = Field(default_factory=list)
    project_type: str | None = None
    stars: int | None = None
    quality_score: float = 0.0
    created_at: str = Field(default_factory=now_utc)
    updated_at: str = Field(default_factory=now_utc)


class RepositorySnapshot(RepoWikiModel):
    id: str
    repo_id: str
    commit_sha: str | None = None
    branch: str | None = None
    indexed_at: str = Field(default_factory=now_utc)
    file_count: int = 0
    line_count: int = 0
    content_hash: str | None = None
    status: str = "completed"


class SourceFile(RepoWikiModel):
    id: str
    snapshot_id: str
    path: str
    language: str | None = None
    mime_type: str | None = None
    size_bytes: int
    line_count: int
    hash: str
    content: str | None = None
    is_test: bool = False
    is_generated: bool = False
    is_dependency: bool = False


class Symbol(RepoWikiModel):
    id: str
    file_id: str
    snapshot_id: str
    name: str
    kind: str
    qualified_name: str
    start_line: int | None = None
    end_line: int | None = None
    signature: str | None = None
    docstring: str | None = None
    visibility: str | None = None


class Dependency(RepoWikiModel):
    id: str
    snapshot_id: str
    manager: str
    name: str
    version_spec: str | None = None
    scope: str | None = None
    manifest_path: str | None = None


class SourceRef(RepoWikiModel):
    id: str
    repo_id: str
    snapshot_id: str
    file_id: str | None = None
    path: str
    start_line: int | None = None
    end_line: int | None = None
    license: str | None = None
    snippet_allowed: bool = False


class KnowledgeObject(RepoWikiModel):
    id: str
    type: KnowledgeType
    title: str
    summary: str
    problem: str | None = None
    solution: str | None = None
    when_to_use: list[str] = Field(default_factory=list)
    when_not_to_use: list[str] = Field(default_factory=list)
    language: str | None = None
    frameworks: list[str] = Field(default_factory=list)
    domain: str | None = None
    project_type: str | None = None
    tags: list[str] = Field(default_factory=list)
    quality_score: float = 0.0
    confidence: float = 0.0
    source_refs: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_utc)
    updated_at: str = Field(default_factory=now_utc)


class GraphNode(RepoWikiModel):
    id: str
    node_type: str
    object_id: str
    label: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(RepoWikiModel):
    id: str
    source_node_id: str
    target_node_id: str
    edge_type: str
    weight: float = 1.0
    confidence: float = 1.0
    source: str = "system"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_utc)


class RetrievalTrace(RepoWikiModel):
    id: str
    task: str
    created_at: str = Field(default_factory=now_utc)
    retrievers_used: list[str] = Field(default_factory=list)
    candidate_count: int = 0
    reranked_count: int = 0
    returned_count: int = 0
    latency_ms: int = 0
    filters: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)


class ContextPack(RepoWikiModel):
    schema_version: str = "context_pack.v1"
    id: str
    task: str
    task_type: str
    constraints: dict[str, Any] = Field(default_factory=dict)
    recommended_patterns: list[dict[str, Any]] = Field(default_factory=list)
    relevant_examples: list[dict[str, Any]] = Field(default_factory=list)
    architecture_rules: list[dict[str, Any]] = Field(default_factory=list)
    implementation_steps: list[str] = Field(default_factory=list)
    tests_to_consider: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    source_citations: list[dict[str, Any]] = Field(default_factory=list)
    answer: str = ""
    retrieval_trace_id: str
    markdown: str = ""
    created_at: str = Field(default_factory=now_utc)


class FeedbackRecord(RepoWikiModel):
    id: str
    context_pack_id: str | None = None
    task_id: str | None = None
    user_rating: int | None = None
    accepted: bool | None = None
    tests_passed: bool | None = None
    lint_passed: bool | None = None
    build_passed: bool | None = None
    merged: bool | None = None
    reviewer_approved: bool | None = None
    rollback: bool | None = None
    incident: bool | None = None
    notes: str | None = None
    created_at: str = Field(default_factory=now_utc)


class StagedKnowledge(RepoWikiModel):
    id: str
    source_feedback_id: str | None = None
    candidate_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0
    dedupe_key: str | None = None
    status: FeedbackStatus = FeedbackStatus.PENDING
    promotion_reason: str | None = None
    created_at: str = Field(default_factory=now_utc)
    updated_at: str = Field(default_factory=now_utc)


class ExtractionResult(RepoWikiModel):
    repository: Repository
    snapshot: RepositorySnapshot
    files: list[SourceFile] = Field(default_factory=list)
    symbols: list[Symbol] = Field(default_factory=list)
    dependencies: list[Dependency] = Field(default_factory=list)
    source_refs: list[SourceRef] = Field(default_factory=list)
    knowledge_objects: list[KnowledgeObject] = Field(default_factory=list)
    graph_nodes: list[GraphNode] = Field(default_factory=list)
    graph_edges: list[GraphEdge] = Field(default_factory=list)
    extraction_events: list[dict[str, Any]] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
