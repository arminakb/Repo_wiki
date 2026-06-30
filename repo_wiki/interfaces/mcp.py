from __future__ import annotations

import json
import sys
from typing import Any

from repo_wiki.core.metrics_service import MetricsService
from repo_wiki.core.reflexion_service import ReflexionService
from repo_wiki.core.retrieval_service import RetrievalService
from repo_wiki.domain.errors import MCPValidationError, RepositoryNotFound
from repo_wiki.logging import log_event
from repo_wiki.storage.sqlite import SQLiteStore


TOOLS = [
    {
        "name": "retrieve_context",
        "description": "Return a cited context pack for a coding task.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "language": {"type": "string"},
                "framework": {"type": "string"},
                "project_type": {"type": "string"},
                "domain": {"type": "string"},
                "repo": {"type": "string"},
                "license_policy": {"type": "string"},
                "max_tokens": {"type": "integer"},
            },
            "required": ["task"],
        },
    },
    {
        "name": "search_knowledge",
        "description": "Search stored knowledge objects.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "type": {"type": "string"},
                "language": {"type": "string"},
                "framework": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "inspect_repository",
        "description": "Return repository metadata and snapshots for one indexed repository.",
        "inputSchema": {
            "type": "object",
            "properties": {"repo_id": {"type": "string"}},
            "required": ["repo_id"],
        },
    },
    {
        "name": "submit_feedback",
        "description": "Submit Reflexion feedback for a context pack.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "context_pack_id": {"type": "string"},
                "accepted": {"type": "boolean"},
                "rating": {"type": "integer"},
                "tests_passed": {"type": "boolean"},
                "lint_passed": {"type": "boolean"},
                "build_passed": {"type": "boolean"},
                "merged": {"type": "boolean"},
                "reviewer_approved": {"type": "boolean"},
                "rollback": {"type": "boolean"},
                "incident": {"type": "boolean"},
                "notes": {"type": "string"},
            },
        },
    },
    {
        "name": "list_feedback",
        "description": "List staged Reflexion feedback records.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
    },
]


def run_stdio_server(store: SQLiteStore) -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            response = handle_json_rpc(request, store)
        except Exception as exc:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32000, "message": str(exc)},
            }
        sys.stdout.write(json.dumps(response, default=str) + "\n")
        sys.stdout.flush()


def handle_json_rpc(request: dict[str, Any], store: SQLiteStore) -> dict[str, Any]:
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": "repo-wiki", "version": "0.1.0"},
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        try:
            result = call_tool(name, arguments, store)
        except Exception as exc:
            return mcp_error(request_id, -32000, exc)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2, sort_keys=True, default=str),
                    }
                ]
            },
        }
    if method == "resources/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": [
                    {"uri": "repo-wiki://metrics", "name": "Metrics"},
                    {"uri": "repo-wiki://repositories", "name": "Repositories"},
                    {"uri": "repo-wiki://repositories/{repo_id}", "name": "Repository"},
                    {
                        "uri": "repo-wiki://knowledge/{knowledge_object_id}",
                        "name": "Knowledge Object",
                    },
                    {"uri": "repo-wiki://context-packs/{context_pack_id}", "name": "Context Pack"},
                    {"uri": "repo-wiki://feedback", "name": "Feedback"},
                ]
            },
        }
    if method == "resources/read":
        uri = params.get("uri")
        if uri == "repo-wiki://metrics":
            payload = MetricsService(store).metrics()
        elif uri == "repo-wiki://repositories":
            payload = [repo.model_dump() for repo in store.list_repositories()]
        elif uri and uri.startswith("repo-wiki://repositories/"):
            repo_id = uri.rsplit("/", 1)[-1]
            payload = store.get_repository(repo_id)
            if payload is None:
                return resource_not_found(request_id, uri)
        elif uri and uri.startswith("repo-wiki://knowledge/"):
            object_id = uri.rsplit("/", 1)[-1]
            obj = store.get_knowledge(object_id)
            if obj is None:
                return resource_not_found(request_id, uri)
            payload = obj.model_dump()
        elif uri and uri.startswith("repo-wiki://context-packs/"):
            context_pack_id = uri.rsplit("/", 1)[-1]
            payload = store.get_context_pack(context_pack_id)
            if payload is None:
                return resource_not_found(request_id, uri)
        elif uri == "repo-wiki://feedback":
            payload = ReflexionService(store).list_staged(status=None)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32602, "message": f"unknown resource: {uri}"},
            }
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(payload, indent=2, sort_keys=True, default=str),
                    }
                ]
            },
        }
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"unknown method: {method}"},
    }


def call_tool(name: str, arguments: dict[str, Any], store: SQLiteStore) -> Any:
    log_event("mcp.tool_call", tool=name)
    if name == "retrieve_context":
        if not arguments.get("task"):
            raise MCPValidationError("task is required")
        result = RetrievalService(store).retrieve(
            arguments["task"],
            language=arguments.get("language"),
            framework=arguments.get("framework"),
            project_type=arguments.get("project_type"),
            domain=arguments.get("domain"),
            repo=arguments.get("repo"),
            max_tokens=int(arguments.get("max_tokens", 4000)),
            license_policy=arguments.get("license_policy"),
        )
        result["citations"] = result["context_pack"].get("source_citations", [])
        return result
    if name == "search_knowledge":
        objects = store.search_knowledge(
            arguments["query"],
            language=arguments.get("language"),
            framework=arguments.get("framework"),
            limit=int(arguments.get("limit", 10)),
        )
        if arguments.get("type"):
            objects = [(obj, score) for obj, score in objects if obj.type == arguments["type"]]
        return [{"object": obj.model_dump(), "score": score} for obj, score in objects]
    if name == "inspect_repository":
        repository = store.get_repository(arguments["repo_id"])
        if repository is None:
            raise RepositoryNotFound(f"repository not found: {arguments['repo_id']}")
        return repository
    if name == "submit_feedback":
        feedback, staged = ReflexionService(store).submit_feedback(
            context_pack_id=arguments.get("context_pack_id"),
            accepted=arguments.get("accepted"),
            rating=arguments.get("rating"),
            tests_passed=arguments.get("tests_passed"),
            lint_passed=arguments.get("lint_passed"),
            build_passed=arguments.get("build_passed"),
            merged=arguments.get("merged"),
            reviewer_approved=arguments.get("reviewer_approved"),
            rollback=arguments.get("rollback"),
            incident=arguments.get("incident"),
            notes=arguments.get("notes"),
        )
        return {"feedback": feedback.model_dump(), "staged": staged.model_dump()}
    if name == "list_feedback":
        return ReflexionService(store).list_staged(
            status=arguments.get("status"),
            limit=int(arguments.get("limit", 20)),
        )
    raise MCPValidationError(f"unknown tool: {name}")


def resource_not_found(request_id: Any, uri: str) -> dict[str, Any]:
    return mcp_error(request_id, -32602, MCPValidationError(f"unknown resource: {uri}"))


def mcp_error(request_id: Any, code: int, exc: Exception) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": str(exc),
            "data": {"type": type(exc).__name__},
        },
    }
