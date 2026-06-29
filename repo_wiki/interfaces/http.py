from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel, Field, ValidationError, field_validator

from repo_wiki.config import Settings
from repo_wiki.core.ingestion_service import IngestionService
from repo_wiki.core.metrics_service import MetricsService
from repo_wiki.core.reflexion_service import ReflexionService
from repo_wiki.core.retrieval_service import RetrievalService
from repo_wiki.domain.errors import (
    LicensePolicyViolation,
    MCPValidationError,
    RepoWikiError,
    RepositoryNotFound,
    RetrievalFailed,
    StorageError,
    UnsupportedSource,
)
from repo_wiki.logging import log_event
from repo_wiki.storage.sqlite import SQLiteStore

MAX_REQUEST_BYTES = 1_000_000
MAX_LIST_LIMIT = 100


class RequestModel(BaseModel):
    model_config = {"extra": "forbid"}


class RepositoryIngestRequest(RequestModel):
    url: str
    branch: str | None = None
    include: list[str] | None = None
    exclude: list[str] | None = None
    license_policy: str | None = None

    @field_validator("url")
    @classmethod
    def require_url(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("url is required")
        return value


class LocalIngestRequest(RequestModel):
    path: str
    include: list[str] | None = None
    exclude: list[str] | None = None
    license_policy: str | None = None

    @field_validator("path")
    @classmethod
    def require_path(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("path is required")
        return value


class RetrieveRequest(RequestModel):
    task: str
    language: str | None = None
    framework: str | None = None
    project_type: str | None = None
    domain: str | None = None
    repo: str | None = None
    max_tokens: int = Field(default=4000, ge=1)
    license_policy: str | None = None
    output_format: str | None = None

    @field_validator("task")
    @classmethod
    def require_task(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("task is required")
        return value


class FeedbackRequest(RequestModel):
    context_pack_id: str | None = None
    accepted: bool | None = None
    rating: int | None = None
    tests_passed: bool | None = None
    lint_passed: bool | None = None
    build_passed: bool | None = None
    merged: bool | None = None
    reviewer_approved: bool | None = None
    rollback: bool | None = None
    incident: bool | None = None
    notes: str | None = None


class StageDecisionRequest(RequestModel):
    reason: str | None = None


def create_app(settings: Settings | None = None, store: SQLiteStore | None = None) -> Any:
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:
        raise RuntimeError("FastAPI is optional; install fastapi to use create_app().") from exc

    active_settings = settings or Settings.from_env()
    active_settings.ensure_dirs()
    active_store = store or SQLiteStore(active_settings.sqlite_path)
    active_store.initialize()
    app = FastAPI(title="Repo Knowledge Compiler", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0", "database": "ok"}

    @app.get("/v1/metrics")
    def metrics() -> dict[str, Any]:
        return MetricsService(active_store).metrics()

    @app.get("/v1/knowledge")
    def knowledge(
        type: str | None = None,
        language: str | None = None,
        framework: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        objects = active_store.list_knowledge(
            type=type,
            language=language,
            framework=framework,
            limit=max(1, min(limit, MAX_LIST_LIMIT)),
        )
        return [obj.model_dump() for obj in objects]

    @app.get("/v1/repositories")
    def repositories(limit: int = 20) -> list[dict[str, Any]]:
        return [
            repo.model_dump()
            for repo in active_store.list_repositories(limit=max(1, min(limit, MAX_LIST_LIMIT)))
        ]

    @app.get("/v1/repositories/{repo_id}")
    def repository(repo_id: str) -> dict[str, Any]:
        payload = active_store.get_repository(repo_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="not found")
        return payload

    @app.post("/v1/ingest/local")
    def ingest_local(payload: LocalIngestRequest) -> dict[str, str]:
        result = IngestionService(active_settings, active_store).ingest_local(
            payload.path,
            license_policy=payload.license_policy,
            include=payload.include,
            exclude=payload.exclude,
        )
        return {
            "repo_id": result.repository.id,
            "snapshot_id": result.snapshot.id,
            "status": "completed",
        }

    @app.post("/v1/ingest/repository")
    def ingest_repository(payload: RepositoryIngestRequest) -> dict[str, str]:
        result = IngestionService(active_settings, active_store).ingest_github(
            payload.url,
            branch=payload.branch,
            license_policy=payload.license_policy,
            include=payload.include,
            exclude=payload.exclude,
        )
        return {
            "repo_id": result.repository.id,
            "snapshot_id": result.snapshot.id,
            "status": "completed",
        }

    @app.post("/v1/retrieve")
    def retrieve(payload: RetrieveRequest) -> dict[str, Any]:
        result = retrieve_from_request(active_store, payload)
        return result

    @app.post("/v1/feedback")
    def feedback(payload: FeedbackRequest) -> dict[str, Any]:
        feedback_record, staged = ReflexionService(active_store).submit_feedback(
            context_pack_id=payload.context_pack_id,
            accepted=payload.accepted,
            rating=payload.rating,
            tests_passed=payload.tests_passed,
            lint_passed=payload.lint_passed,
            build_passed=payload.build_passed,
            merged=payload.merged,
            reviewer_approved=payload.reviewer_approved,
            rollback=payload.rollback,
            incident=payload.incident,
            notes=payload.notes,
        )
        return {"feedback": feedback_record.model_dump(), "staged": staged.model_dump()}

    @app.post("/v1/feedback/{stage_id}/promote")
    def promote(stage_id: str, payload: StageDecisionRequest) -> dict[str, Any]:
        return ReflexionService(active_store).promote_staged(stage_id, reason=payload.reason)

    @app.post("/v1/feedback/{stage_id}/reject")
    def reject(stage_id: str, payload: StageDecisionRequest) -> dict[str, Any]:
        return ReflexionService(active_store).reject_staged(stage_id, reason=payload.reason)

    return app


def serve(host: str, port: int, store: SQLiteStore | None = None) -> None:
    settings = Settings.from_env()
    settings.ensure_dirs()
    active_store = store or SQLiteStore(settings.sqlite_path)
    active_store.initialize()

    class Handler(RepoWikiHandler):
        settings_ref = settings
        store_ref = active_store

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Repo Knowledge Compiler API listening on http://{host}:{port}")
    server.serve_forever()


class RepoWikiHandler(BaseHTTPRequestHandler):
    settings_ref: Settings
    store_ref: SQLiteStore

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.respond({"status": "ok", "version": "0.1.0", "database": "ok"})
            return
        if parsed.path == "/v1/metrics":
            self.respond(MetricsService(self.store_ref).metrics())
            return
        if parsed.path == "/v1/knowledge":
            query = parse_qs(parsed.query)
            objects = self.store_ref.list_knowledge(
                type=first(query, "type"),
                language=first(query, "language"),
                framework=first(query, "framework"),
                limit=bounded_int(
                    first(query, "limit"),
                    default=20,
                    minimum=1,
                    maximum=MAX_LIST_LIMIT,
                ),
            )
            self.respond([obj.model_dump() for obj in objects])
            return
        if parsed.path == "/v1/repositories":
            query = parse_qs(parsed.query)
            repositories = self.store_ref.list_repositories(
                limit=bounded_int(
                    first(query, "limit"),
                    default=20,
                    minimum=1,
                    maximum=MAX_LIST_LIMIT,
                )
            )
            self.respond([repo.model_dump() for repo in repositories])
            return
        if parsed.path.startswith("/v1/repositories/"):
            repo_id = parsed.path.rsplit("/", 1)[-1]
            repository = self.store_ref.get_repository(repo_id)
            if repository is None:
                self.not_found()
                return
            self.respond(repository)
            return
        self.not_found()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self.read_json()
            if parsed.path == "/v1/ingest/local":
                request = LocalIngestRequest(**payload)
                result = IngestionService(self.settings_ref, self.store_ref).ingest_local(
                    request.path,
                    license_policy=request.license_policy,
                    include=request.include,
                    exclude=request.exclude,
                )
                self.respond(
                    {
                        "repo_id": result.repository.id,
                        "snapshot_id": result.snapshot.id,
                        "status": "completed",
                    }
                )
                return
            if parsed.path == "/v1/ingest/repository":
                request = RepositoryIngestRequest(**payload)
                result = IngestionService(self.settings_ref, self.store_ref).ingest_github(
                    request.url,
                    branch=request.branch,
                    license_policy=request.license_policy,
                    include=request.include,
                    exclude=request.exclude,
                )
                self.respond(
                    {
                        "repo_id": result.repository.id,
                        "snapshot_id": result.snapshot.id,
                        "status": "completed",
                    }
                )
                return
            if parsed.path == "/v1/retrieve":
                self.respond(retrieve_from_request(self.store_ref, RetrieveRequest(**payload)))
                return
            if parsed.path == "/v1/feedback":
                request = FeedbackRequest(**payload)
                feedback, staged = ReflexionService(self.store_ref).submit_feedback(
                    context_pack_id=request.context_pack_id,
                    accepted=request.accepted,
                    rating=request.rating,
                    tests_passed=request.tests_passed,
                    lint_passed=request.lint_passed,
                    build_passed=request.build_passed,
                    merged=request.merged,
                    reviewer_approved=request.reviewer_approved,
                    rollback=request.rollback,
                    incident=request.incident,
                    notes=request.notes,
                )
                self.respond({"feedback": feedback.model_dump(), "staged": staged.model_dump()})
                return
            if parsed.path.startswith("/v1/feedback/") and parsed.path.endswith("/promote"):
                request = StageDecisionRequest(**payload)
                stage_id = parsed.path.split("/")[-2]
                result = ReflexionService(self.store_ref).promote_staged(
                    stage_id, reason=request.reason
                )
                self.respond(result)
                return
            if parsed.path.startswith("/v1/feedback/") and parsed.path.endswith("/reject"):
                request = StageDecisionRequest(**payload)
                stage_id = parsed.path.split("/")[-2]
                result = ReflexionService(self.store_ref).reject_staged(
                    stage_id, reason=request.reason
                )
                self.respond(result)
                return
            self.not_found()
        except Exception as exc:
            status, payload = http_error(exc)
            self.respond(payload, status=status)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_REQUEST_BYTES:
            raise ValueError("request body too large")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        payload = json.loads(raw or "{}")
        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")
        return payload

    def respond(self, payload: Any, status: int = 200) -> None:
        log_event("api.request", path=self.path, status=status)
        raw = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def not_found(self) -> None:
        self.respond({"error": {"type": "NotFound", "message": "not found"}}, status=404)

    def log_message(self, format: str, *args: Any) -> None:
        return


def error_payload(exc: Exception) -> dict[str, Any]:
    return {"error": {"type": type(exc).__name__, "message": str(exc)}}


def http_error(exc: Exception) -> tuple[int, dict[str, Any]]:
    if isinstance(exc, RepositoryNotFound):
        return 404, error_payload(exc)
    if isinstance(exc, (UnsupportedSource, LicensePolicyViolation, MCPValidationError, ValidationError)):
        return 400, error_payload(exc)
    if isinstance(exc, RetrievalFailed):
        return 422, error_payload(exc)
    if isinstance(exc, StorageError):
        return 503, error_payload(exc)
    if isinstance(exc, (ValueError, KeyError, TypeError, json.JSONDecodeError)):
        return 400, error_payload(exc)
    if isinstance(exc, RepoWikiError):
        return 409, error_payload(exc)
    return 500, error_payload(exc)


def first(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    return values[0] if values else None


def bounded_int(
    value: str | None,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    try:
        parsed = int(value) if value is not None else default
    except ValueError:
        return default
    return max(minimum, min(parsed, maximum))


def retrieve_from_request(store: SQLiteStore, request: RetrieveRequest) -> dict[str, Any]:
    result = RetrievalService(store).retrieve(
        request.task,
        language=request.language,
        framework=request.framework,
        project_type=request.project_type,
        domain=request.domain,
        repo=request.repo,
        max_tokens=request.max_tokens,
        license_policy=request.license_policy,
    )
    return result
