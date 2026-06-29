from __future__ import annotations

import json
import contextlib
import io
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from repo_wiki.benchmarks.report import write_benchmark_report
from repo_wiki.config import Settings
from repo_wiki.core.ingestion_service import IngestionService
from repo_wiki.core.metrics_service import MetricsService
from repo_wiki.core.reflexion_service import ReflexionService
from repo_wiki.core.retrieval_service import RetrievalService
from repo_wiki.domain.models import SourceFile
from repo_wiki.inspector.detector import LocalProjectInspector
from repo_wiki.extract.file_tree import redact_secrets
from repo_wiki.extract.typescript import extract_ts_imports, extract_ts_symbols
from repo_wiki.ingest.filters import is_text_candidate, should_skip_path
from repo_wiki.interfaces.cli import main
from repo_wiki.interfaces import http
from repo_wiki.interfaces.http import create_app
from repo_wiki.interfaces.mcp import handle_json_rpc
from repo_wiki.live.engine import LiveResearchEngine
from repo_wiki.storage.sqlite import SQLiteStore


class EndToEndTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "sample"
        self.repo.mkdir()
        (self.repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        (self.repo / "README.md").write_text("# Sample\n\nFastAPI auth service.\n", encoding="utf-8")
        (self.repo / "requirements.txt").write_text("fastapi>=0.100\npytest>=8\n", encoding="utf-8")
        (self.repo / "package.json").write_text(
            json.dumps({"dependencies": {"next": "^14.0.0", "react": "^18.0.0"}}),
            encoding="utf-8",
        )
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "guide.md").write_text(
            "# Guide\n\n## API\n\n```ts\nfetch('/api/users')\n```\n\n[Home](../README.md)\n",
            encoding="utf-8",
        )
        route_dir = self.repo / "app" / "api" / "users"
        route_dir.mkdir(parents=True)
        (route_dir / "route.ts").write_text(
            "export async function GET() {\n  return Response.json([])\n}\n",
            encoding="utf-8",
        )
        (self.repo / "auth.py").write_text(
            "\n".join(
                [
                    "from fastapi import APIRouter",
                    "",
                    "router = APIRouter()",
                    "",
                    "class TokenService:",
                    "    def issue_token(self, user_id: str) -> str:",
                    "        return user_id",
                    "",
                    "def is_valid_user(user_id: str) -> bool:",
                    "    return bool(user_id)",
                    "",
                    "def reset_password(user_id: str) -> bool:",
                    "    return is_valid_user(user_id)",
                ]
            ),
            encoding="utf-8",
        )
        tests_dir = self.repo / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_auth.py").write_text(
            "from auth import reset_password\n\n\ndef test_reset_password():\n    assert reset_password('u1')\n",
            encoding="utf-8",
        )
        self.settings = Settings(
            data_dir=self.root / ".repo-wiki",
            sqlite_path=self.root / ".repo-wiki" / "repo-wiki.db",
            clone_dir=self.root / ".repo-wiki" / "clones",
            vault_path=self.root / ".repo-wiki" / "vault",
        )
        self.settings.ensure_dirs()
        self.store = SQLiteStore(self.settings.sqlite_path)
        self.store.initialize()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_ingest_retrieve_feedback_and_mcp(self) -> None:
        result = IngestionService(self.settings, self.store).ingest_local(self.repo)
        self.assertEqual(result.repository.primary_language, "Python")
        self.assertIn("FastAPI", result.repository.detected_frameworks)
        self.assertGreaterEqual(len(result.knowledge_objects), 2)
        self.assertGreater(len(result.graph_edges), 0)
        self.assertEqual(result.metrics["files"], len(result.files))
        self.assertIn("knowledge_compilation", {event["stage"] for event in result.extraction_events})
        self.assertIn("CALLS", {edge.edge_type for edge in result.graph_edges})

        retrieved = RetrievalService(self.store).retrieve(
            "implement password reset auth endpoint with FastAPI tests",
            language="Python",
            framework="FastAPI",
            domain="auth",
        )
        pack = retrieved["context_pack"]
        self.assertEqual(pack["task_type"], "test_generation")
        self.assertTrue(pack["source_citations"])
        self.assertIn("trace_", retrieved["trace_id"])
        tiny = RetrievalService(self.store).retrieve(
            "implement password reset auth endpoint with FastAPI tests",
            language="Python",
            framework="FastAPI",
            domain="auth",
            max_tokens=40,
        )
        self.assertLessEqual(len(tiny["markdown"].split()), 80)
        self.assertTrue(
            any(
                "vector score" in reason
                for section in (
                    pack["recommended_patterns"],
                    pack["relevant_examples"],
                    pack["architecture_rules"],
                )
                for item in section
                for reason in item["why_relevant"]
            )
        )
        trace = self.store.get_retrieval_trace(retrieved["trace_id"])
        self.assertIn("source", trace["payload"]["candidate_counts"])
        self.assertIn("ranking_details", trace["payload"])
        self.assertIsNotNone(self.store.get_repository(result.repository.id))
        self.assertTrue(self.store.list_repositories())

        reflexion = ReflexionService(self.store)
        feedback, staged = reflexion.submit_feedback(
            context_pack_id=pack["id"],
            accepted=True,
            rating=5,
            tests_passed=True,
            lint_passed=True,
            build_passed=True,
            reviewer_approved=True,
            incident=False,
        )
        self.assertTrue(feedback.accepted)
        self.assertTrue(feedback.reviewer_approved)
        self.assertFalse(feedback.incident)
        self.assertEqual(staged.status, "pending")
        self.assertGreaterEqual(staged.score, 0.9)
        promoted = reflexion.promote_staged(staged.id, reason="reviewed")
        self.assertEqual(promoted["status"], "promoted")
        self.assertIsNotNone(promoted["promoted_object_id"])
        with self.assertRaises(ValueError):
            reflexion.reject_staged(staged.id, reason="too late")
        _, duplicate_staged = reflexion.submit_feedback(
            context_pack_id=pack["id"],
            accepted=False,
            rating=2,
            notes="duplicate",
        )
        rejected = reflexion.reject_staged(duplicate_staged.id, reason="duplicate")
        self.assertEqual(rejected["status"], "rejected")

        response = handle_json_rpc(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "retrieve_context",
                    "arguments": {
                        "task": "add FastAPI auth tests",
                        "language": "Python",
                        "framework": "FastAPI",
                    },
                },
            },
            self.store,
        )
        self.assertEqual(response["id"], 1)
        text = response["result"]["content"][0]["text"]
        self.assertIn("context_pack", json.loads(text))

        feedback_response = handle_json_rpc(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "submit_feedback",
                    "arguments": {
                        "context_pack_id": pack["id"],
                        "accepted": True,
                        "tests_passed": True,
                        "reviewer_approved": True,
                        "incident": False,
                        "notes": "useful",
                    },
                },
            },
            self.store,
        )
        feedback_text = feedback_response["result"]["content"][0]["text"]
        self.assertTrue(json.loads(feedback_text)["feedback"]["reviewer_approved"])

        repository_response = handle_json_rpc(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "inspect_repository",
                    "arguments": {"repo_id": result.repository.id},
                },
            },
            self.store,
        )
        repository_text = repository_response["result"]["content"][0]["text"]
        self.assertEqual(json.loads(repository_text)["repository"]["id"], result.repository.id)

        resource = handle_json_rpc(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "resources/read",
                "params": {"uri": "repo-wiki://metrics"},
            },
            self.store,
        )
        self.assertEqual(resource["id"], 2)
        self.assertIn("indexed_repositories", resource["result"]["contents"][0]["text"])

        context_resource = handle_json_rpc(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {"uri": f"repo-wiki://context-packs/{pack['id']}"},
            },
            self.store,
        )
        self.assertEqual(context_resource["id"], 4)
        self.assertIn(pack["id"], context_resource["result"]["contents"][0]["text"])

        report_path = self.root / "mvp-results.md"
        metrics = write_benchmark_report(self.store, report_path)
        report_text = report_path.read_text(encoding="utf-8")
        self.assertTrue(report_path.exists())
        self.assertGreaterEqual(metrics["indexed_repositories"], 1)
        self.assertIn("Retrieval Quality Suite", report_text)
        self.assertIn("Average latency", report_text)
        self.assertIn("Candidate Counts", report_text)
        self.assertIn("Citation coverage", report_text)
        self.assertGreaterEqual(metrics["benchmark_tasks"], 5)
        self.assertIn("average_latency_ms", metrics)

        graph_path = self.root / "knowledge-graph.mmd"
        graph_path.write_text(self.store.export_graph_mermaid(limit=10), encoding="utf-8")
        graph_text = graph_path.read_text(encoding="utf-8")
        self.assertTrue(graph_text.startswith("flowchart TD"))
        self.assertIn("TESTED_BY", {edge.edge_type for edge in result.graph_edges})

    def test_fastapi_app_factory_reports_missing_optional_dependency(self) -> None:
        try:
            app = create_app(self.settings, self.store)
        except RuntimeError as exc:
            self.assertIn("FastAPI is optional", str(exc))
        else:
            self.assertEqual(app.title, "Repo Knowledge Compiler")

    def test_default_excludes_skip_generated_repo_wiki_and_agent_dirs(self) -> None:
        self.assertTrue(should_skip_path(self.repo / ".repo-wiki" / "repo-wiki.db", self.repo))
        self.assertTrue(should_skip_path(self.repo / ".skills" / "skill" / "SKILL.md", self.repo))
        self.assertTrue(should_skip_path(self.repo / "vendor" / "lib.py", self.repo))
        self.assertFalse(is_text_candidate(self.repo / ".env"))
        self.assertEqual(
            redact_secrets("API_KEY='super-secret-value'"),
            "[REDACTED_SECRET]",
        )

    def test_ingest_include_exclude_patterns(self) -> None:
        result = IngestionService(self.settings, self.store).ingest_local(
            self.repo,
            include=["**/*.py"],
            exclude=["tests/**"],
        )
        self.assertTrue(result.files)
        self.assertTrue(all(file.path.endswith(".py") for file in result.files))
        self.assertFalse(any(file.is_test for file in result.files))

    def test_implementation_citations_use_symbol_line_ranges(self) -> None:
        result = IngestionService(self.settings, self.store).ingest_local(self.repo)
        refs = {ref.id: ref for ref in result.source_refs}
        auth_pattern = next(
            obj
            for obj in result.knowledge_objects
            if obj.payload.get("path") == "auth.py"
        )

        cited_ranges = [
            (refs[ref_id].start_line, refs[ref_id].end_line)
            for ref_id in auth_pattern.source_refs
        ]

        self.assertIn((5, 13), cited_ranges)
        self.assertNotIn((1, 12), cited_ranges)

    def test_metadata_only_retrieval_keeps_metadata_citations(self) -> None:
        IngestionService(self.settings, self.store).ingest_local(
            self.repo,
            license_policy="metadata_only",
        )

        pack = RetrievalService(self.store).retrieve(
            "implement password reset auth endpoint with FastAPI tests",
            language="Python",
            framework="FastAPI",
            domain="auth",
            license_policy="metadata_only",
        )["context_pack"]

        self.assertTrue(pack["source_citations"])
        self.assertTrue(all(citation["snippet_allowed"] is False for citation in pack["source_citations"]))
        for section in (
            pack["recommended_patterns"],
            pack["relevant_examples"],
            pack["architecture_rules"],
        ):
            self.assertTrue(all(citation["snippet_allowed"] is False for item in section for citation in item["citations"]))

    def test_core_extractors_cover_typescript_routes_docs_packages_and_tests(self) -> None:
        result = IngestionService(self.settings, self.store).ingest_local(self.repo)
        graph_types = {edge.edge_type for edge in result.graph_edges}
        route_pattern = next(
            obj
            for obj in result.knowledge_objects
            if obj.payload.get("path") == "app/api/users/route.ts"
        )
        architecture_pattern = next(
            obj
            for obj in result.knowledge_objects
            if obj.type == "ArchitecturePattern"
        )

        self.assertIn("next", {dep.name for dep in result.dependencies})
        self.assertIn("DEFINES_ROUTE", graph_types)
        self.assertIn("HANDLES_ENDPOINT", graph_types)
        self.assertIn("TESTED_BY", graph_types)
        self.assertEqual(route_pattern.payload["routes"][0]["path"], "/api/users")
        self.assertEqual(route_pattern.payload["routes"][0]["method"], "GET")
        guide_doc = next(doc for doc in architecture_pattern.payload["docs"] if doc["code_fences"])
        self.assertEqual(guide_doc["code_fences"][0]["language"], "ts")
        self.assertEqual(guide_doc["links"][0]["target"], "../README.md")

    def test_typescript_extractor_ignores_comments_strings_and_spans_blocks(self) -> None:
        file = SourceFile(
            id="file_ts",
            snapshot_id="snap_ts",
            path="app/api/users/route.tsx",
            language="TypeScript",
            size_bytes=0,
            line_count=22,
            hash="hash",
            content="\n".join(
                [
                    'import React from "react";',
                    "const fake = `",
                    'import bad from "bad";',
                    "`;",
                    "/*",
                    "export function Ignored() {}",
                    "*/",
                    "export type User = {",
                    "  id: string",
                    "};",
                    'export { helper } from "./helper";',
                    "export const UserCard = (",
                    "  props: { user: User }",
                    ") => {",
                    "  return <div>{props.user.id}</div>;",
                    "};",
                    "export async function GET(",
                    "  request: Request",
                    ") {",
                    "  return Response.json({});",
                    "}",
                ]
            ),
        )

        imports = extract_ts_imports(file)
        symbols = extract_ts_symbols(file)
        by_name = {symbol.name: symbol for symbol in symbols}

        self.assertEqual(imports, ["./helper", "react"])
        self.assertNotIn("Ignored", by_name)
        self.assertEqual(by_name["User"].kind, "type")
        self.assertEqual(by_name["User"].end_line, 10)
        self.assertEqual(by_name["UserCard"].kind, "component")
        self.assertEqual(by_name["UserCard"].end_line, 16)
        self.assertTrue(any(symbol.name == "GET" and symbol.kind == "route" for symbol in symbols))

    def test_ingest_skips_custom_data_dir_inside_repo(self) -> None:
        custom_settings = Settings(
            data_dir=self.repo / ".custom-repo-wiki",
            sqlite_path=self.repo / ".custom-repo-wiki" / "repo-wiki.db",
            clone_dir=self.repo / ".custom-repo-wiki" / "clones",
            vault_path=self.repo / ".custom-repo-wiki" / "vault",
        )
        custom_settings.ensure_dirs()
        (custom_settings.vault_path / "generated.md").write_text(
            "# Generated\n\nShould not be indexed.\n",
            encoding="utf-8",
        )
        store = SQLiteStore(custom_settings.sqlite_path)
        store.initialize()

        result = IngestionService(custom_settings, store).ingest_local(self.repo)

        self.assertNotIn(".custom-repo-wiki/vault/generated.md", {file.path for file in result.files})

    def test_repo_wiki_toml_config_and_env_overrides(self) -> None:
        config_root = self.root / "configured"
        config_root.mkdir()
        (config_root / "repo-wiki.toml").write_text(
            "\n".join(
                [
                    "[storage]",
                    'data_dir = ".knowledge"',
                    'sqlite_path = ".knowledge/custom.db"',
                    "",
                    "[ingestion]",
                    "max_file_size_bytes = 1234",
                    'default_excludes = ["node_modules", ".cache"]',
                    "",
                    "[retrieval]",
                    "max_tokens = 321",
                    "",
                    "[license]",
                    'policy = "metadata_only"',
                    "",
                    "[llm]",
                    'provider = "disabled"',
                ]
            ),
            encoding="utf-8",
        )
        old_db = os.environ.get("REPO_WIKI_DB")
        os.environ["REPO_WIKI_DB"] = str(config_root / "override.db")
        try:
            settings = Settings.from_env(config_root)
        finally:
            if old_db is None:
                os.environ.pop("REPO_WIKI_DB", None)
            else:
                os.environ["REPO_WIKI_DB"] = old_db

        self.assertEqual(settings.data_dir, config_root / ".knowledge")
        self.assertEqual(settings.sqlite_path, config_root / "override.db")
        self.assertEqual(settings.clone_dir, config_root / ".knowledge" / "clones")
        self.assertEqual(settings.vault_path, config_root / ".knowledge" / "vault")
        self.assertEqual(settings.max_file_size_bytes, 1234)
        self.assertEqual(settings.license_policy, "metadata_only")
        self.assertEqual(settings.default_excludes, ("node_modules", ".cache"))
        self.assertEqual(settings.default_max_tokens, 321)
        self.assertIsNone(settings.llm_provider)

    def test_storage_schema_version_is_recorded(self) -> None:
        store = SQLiteStore(self.root / "schema-version.db")
        store.initialize()

        self.assertEqual(store.schema_version(), "0003_promoted_knowledge_link")
        with store.connect() as conn:
            self.assertEqual(
                [row["id"] for row in conn.execute("SELECT id FROM schema_migrations ORDER BY id")],
                [
                    "0001_initial_schema",
                    "0002_feedback_objective_signals",
                    "0003_promoted_knowledge_link",
                ],
            )

    def test_storage_initialize_upgrades_legacy_schema_without_losing_rows(self) -> None:
        db_path = self.root / "legacy-schema.db"
        with contextlib.closing(sqlite3.connect(db_path)) as conn:
            conn.executescript(
                """
                CREATE TABLE feedback_records (
                  id TEXT PRIMARY KEY,
                  context_pack_id TEXT,
                  task_id TEXT,
                  user_rating INTEGER,
                  accepted INTEGER,
                  tests_passed INTEGER,
                  lint_passed INTEGER,
                  build_passed INTEGER,
                  merged INTEGER,
                  rollback INTEGER,
                  notes TEXT,
                  created_at TEXT NOT NULL
                );
                CREATE TABLE staged_knowledge (
                  id TEXT PRIMARY KEY,
                  source_feedback_id TEXT,
                  candidate_type TEXT NOT NULL,
                  payload_json TEXT NOT NULL,
                  score REAL NOT NULL DEFAULT 0,
                  dedupe_key TEXT,
                  status TEXT NOT NULL,
                  promotion_reason TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                CREATE TABLE schema_migrations (
                  id TEXT PRIMARY KEY,
                  applied_at TEXT NOT NULL
                );
                INSERT INTO feedback_records (
                  id, context_pack_id, task_id, user_rating, accepted, tests_passed,
                  lint_passed, build_passed, merged, rollback, notes, created_at
                )
                VALUES (
                  'feedback_legacy', NULL, 'task_1', 5, 1, 1, 1, 1, 1, 0,
                  'legacy row', '2026-01-01T00:00:00Z'
                );
                INSERT INTO staged_knowledge (
                  id, source_feedback_id, candidate_type, payload_json, score,
                  dedupe_key, status, promotion_reason, created_at, updated_at
                )
                VALUES (
                  'staged_legacy', 'feedback_legacy', 'ImplementationPattern', '{}',
                  0.9, 'key', 'pending', NULL,
                  '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
                );
                INSERT INTO schema_migrations (id, applied_at)
                VALUES ('0001_initial_schema', '2026-01-01T00:00:00Z');
                """
            )
            conn.commit()

        store = SQLiteStore(db_path)
        store.initialize()

        self.assertEqual(store.schema_version(), "0003_promoted_knowledge_link")
        with store.connect() as conn:
            feedback_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(feedback_records)")
            }
            staged_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(staged_knowledge)")
            }
            feedback = conn.execute(
                "SELECT reviewer_approved, incident, notes FROM feedback_records WHERE id = ?",
                ("feedback_legacy",),
            ).fetchone()
            staged = conn.execute(
                "SELECT promoted_object_id, status FROM staged_knowledge WHERE id = ?",
                ("staged_legacy",),
            ).fetchone()

        self.assertIn("reviewer_approved", feedback_columns)
        self.assertIn("incident", feedback_columns)
        self.assertIn("promoted_object_id", staged_columns)
        self.assertEqual(feedback["notes"], "legacy row")
        self.assertEqual(staged["status"], "pending")

    def test_benchmark_ingest_list_accepts_comment_only_file(self) -> None:
        repos = self.root / "repos.txt"
        repos.write_text("# add repository URLs here\n", encoding="utf-8")
        old_data_dir = os.environ.get("REPO_WIKI_DATA_DIR")
        os.environ["REPO_WIKI_DATA_DIR"] = str(self.root / ".cli-repo-wiki")
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["benchmark", "ingest-list", str(repos)]), 0)
        finally:
            if old_data_dir is None:
                os.environ.pop("REPO_WIKI_DATA_DIR", None)
            else:
                os.environ["REPO_WIKI_DATA_DIR"] = old_data_dir

    def test_strategy_command_aliases_and_stack_detector(self) -> None:
        IngestionService(self.settings, self.store).ingest_local(self.repo)
        stack = LocalProjectInspector().detect_stack(self.repo)
        self.assertIn("Python", stack.languages)
        self.assertIn("FastAPI", stack.frameworks)
        self.assertIn("pytest", stack.test_tools)

        old_data_dir = os.environ.get("REPO_WIKI_DATA_DIR")
        os.environ["REPO_WIKI_DATA_DIR"] = str(self.settings.data_dir)
        try:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["status"]), 0)
            self.assertIn("Knowledge Objects", output.getvalue())

            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["doctor"]), 0)
            self.assertIn("SQLite integrity", output.getvalue())

            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(
                    main(
                        [
                            "query",
                            "implement FastAPI auth tests",
                            "--profile",
                            "local_small",
                            "--format",
                            "json",
                        ]
                    ),
                    0,
                )
            payload = json.loads(output.getvalue())
            self.assertIn("context_pack", payload)
            self.assertIn("quality", payload)

            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["bootstrap", "--list"]), 0)
            self.assertIn("python-web-apis", output.getvalue())
        finally:
            if old_data_dir is None:
                os.environ.pop("REPO_WIKI_DATA_DIR", None)
            else:
                os.environ["REPO_WIKI_DATA_DIR"] = old_data_dir

    def test_phase3_interface_contracts_are_consistent(self) -> None:
        result = IngestionService(self.settings, self.store).ingest_local(self.repo)
        pack = RetrievalService(self.store).retrieve(
            "implement password reset auth endpoint with FastAPI tests",
            language="Python",
            framework="FastAPI",
        )["context_pack"]
        feedback, staged = ReflexionService(self.store).submit_feedback(
            context_pack_id=pack["id"],
            accepted=True,
            rating=5,
            tests_passed=True,
        )

        old_data_dir = os.environ.get("REPO_WIKI_DATA_DIR")
        os.environ["REPO_WIKI_DATA_DIR"] = str(self.settings.data_dir)
        try:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["ingest", "status", "job_123"]), 0)
            self.assertIn("completed", output.getvalue())

            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["extract", result.repository.id]), 0)
            self.assertIn("snapshot_id", output.getvalue())

            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["compile", result.repository.id, "--no-llm"]), 0)
            self.assertIn("knowledge_objects", output.getvalue())
        finally:
            if old_data_dir is None:
                os.environ.pop("REPO_WIKI_DATA_DIR", None)
            else:
                os.environ["REPO_WIKI_DATA_DIR"] = old_data_dir

        self.assertEqual(
            http.RetrieveRequest(task="x", repo=result.repository.id).repo,
            result.repository.id,
        )
        with self.assertRaises(ValueError):
            http.LocalIngestRequest(path="")

        health = object.__new__(http.RepoWikiHandler)
        health.store_ref = self.store
        health.settings_ref = self.settings
        health.path = "/health"
        health.wfile = io.BytesIO()
        health.send_response = lambda status: setattr(health, "status", status)
        health.send_header = lambda *args: None
        health.end_headers = lambda: None
        http.RepoWikiHandler.do_GET(health)
        self.assertEqual(health.status, 200)
        self.assertEqual(json.loads(health.wfile.getvalue())["status"], "ok")

        body = json.dumps(
            {"task": "add FastAPI auth tests", "repo": result.repository.id}
        ).encode("utf-8")
        retrieve_handler = object.__new__(http.RepoWikiHandler)
        retrieve_handler.store_ref = self.store
        retrieve_handler.settings_ref = self.settings
        retrieve_handler.path = "/v1/retrieve"
        retrieve_handler.headers = {"Content-Length": str(len(body))}
        retrieve_handler.rfile = io.BytesIO(body)
        retrieve_handler.wfile = io.BytesIO()
        retrieve_handler.send_response = lambda status: setattr(
            retrieve_handler, "status", status
        )
        retrieve_handler.send_header = lambda *args: None
        retrieve_handler.end_headers = lambda: None
        http.RepoWikiHandler.do_POST(retrieve_handler)
        retrieve_payload = json.loads(retrieve_handler.wfile.getvalue())
        self.assertEqual(retrieve_handler.status, 200)
        self.assertEqual(
            retrieve_payload["context_pack"]["constraints"]["repo"],
            result.repository.id,
        )

        retrieved = handle_json_rpc(
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {
                    "name": "retrieve_context",
                    "arguments": {
                        "task": "add FastAPI auth tests",
                        "repo": result.repository.id,
                    },
                },
            },
            self.store,
        )
        retrieved_payload = json.loads(retrieved["result"]["content"][0]["text"])
        self.assertIn("citations", retrieved_payload)
        self.assertEqual(
            retrieved_payload["context_pack"]["constraints"]["repo"],
            result.repository.id,
        )

        feedback_list = handle_json_rpc(
            {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "list_feedback",
                    "arguments": {"status": "pending"},
                },
            },
            self.store,
        )
        feedback_payload = json.loads(feedback_list["result"]["content"][0]["text"])
        self.assertTrue(any(item["source_feedback_id"] == feedback.id for item in feedback_payload))
        self.assertTrue(any(item["id"] == staged.id for item in feedback_payload))

        resources = handle_json_rpc(
            {"jsonrpc": "2.0", "id": 9, "method": "resources/list"},
            self.store,
        )["result"]["resources"]
        self.assertIn(
            "repo-wiki://feedback",
            {resource["uri"] for resource in resources},
        )

    def test_phase4_retrieval_prioritizes_query_context_and_records_ranking_details(self) -> None:
        quality_repo = self.root / "quality"
        quality_repo.mkdir()
        (quality_repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        (quality_repo / "README.md").write_text("# Quality\n\nGraphRAG query context docs.\n")
        package_dir = quality_repo / "packages" / "graphrag" / "query"
        package_dir.mkdir(parents=True)
        (package_dir / "context_builder.py").write_text(
            "\n".join(
                [
                    "class QueryContextBuilder:",
                    "    def build_query_context(self, entities, relationships):",
                    "        return {'entities': entities, 'relationships': relationships}",
                    "",
                    "def build_query_context(task):",
                    "    return QueryContextBuilder().build_query_context([], [])",
                ]
            ),
            encoding="utf-8",
        )
        (package_dir / "vector_store.py").write_text(
            "\n".join(
                [
                    "class VectorStore:",
                    "    def search(self, query):",
                    "        return []",
                ]
            ),
            encoding="utf-8",
        )
        IngestionService(self.settings, self.store).ingest_local(quality_repo)

        result = RetrievalService(self.store).retrieve(
            "how does GraphRAG build query context",
            limit=3,
        )
        pack = result["context_pack"]
        first_pattern = pack["recommended_patterns"][0]
        trace = self.store.get_retrieval_trace(result["trace_id"])

        self.assertIn(first_pattern["type"], {"CodeExample", "ImplementationPattern"})
        self.assertEqual(first_pattern["citations"][0]["path"], "packages/graphrag/query/context_builder.py")
        self.assertIn("build_query_context", first_pattern["summary"])
        self.assertIn("candidate_counts", trace["payload"])
        self.assertIn("source", trace["payload"]["candidate_counts"])
        self.assertIn("ranking_details", trace["payload"])
        self.assertEqual(
            trace["payload"]["ranking_details"][0]["path"],
            "packages/graphrag/query/context_builder.py",
        )
        self.assertLessEqual(len(result["markdown"].split()), 900)

    def test_live_fallback_indexes_one_repo_without_network_in_tests(self) -> None:
        repo_candidate = mock.Mock(url="https://github.com/example/project")
        retrieved = {"context_pack": {"source_citations": []}, "markdown": "", "trace_id": "trace_1"}
        with (
            mock.patch("repo_wiki.live.engine.discover_repositories", return_value=[repo_candidate]),
            mock.patch.object(IngestionService, "ingest_github") as ingest_github,
            mock.patch.object(RetrievalService, "retrieve", return_value=retrieved) as retrieve,
        ):
            result = LiveResearchEngine(self.settings, self.store).search("FastAPI auth")
        ingest_github.assert_called_once_with("https://github.com/example/project")
        retrieve.assert_called_once()
        self.assertEqual(result["trace_id"], "trace_1")

    def test_phase6_reliability_security_and_backup_contracts(self) -> None:
        malicious = self.root / "malicious"
        malicious.mkdir()
        (malicious / "LICENSE").write_text("GPL\n", encoding="utf-8")
        (malicious / ".env").write_text("API_KEY='should-not-index'\n", encoding="utf-8")
        (malicious / "secret.py").write_text(
            "\n".join(
                [
                    "TOKEN='super-secret-value'",
                    "KEY='-----BEGIN PRIVATE KEY-----abc-----END PRIVATE KEY-----'",
                    "",
                    "def handle_secret():",
                    "    return TOKEN",
                ]
            ),
            encoding="utf-8",
        )
        (malicious / "large.py").write_text("x" * 200, encoding="utf-8")
        outside = self.root / "outside.py"
        outside.write_text("print('outside')\n", encoding="utf-8")
        (malicious / "outside_link.py").symlink_to(outside)
        (malicious / "binary.py").write_bytes(b"safe = 1\n\0hidden")

        strict_settings = Settings(
            data_dir=self.root / ".strict-repo-wiki",
            sqlite_path=self.root / ".strict-repo-wiki" / "repo-wiki.db",
            clone_dir=self.root / ".strict-repo-wiki" / "clones",
            vault_path=self.root / ".strict-repo-wiki" / "vault",
            max_file_size_bytes=150,
        )
        strict_settings.ensure_dirs()
        strict_store = SQLiteStore(strict_settings.sqlite_path)
        strict_store.initialize()

        with self.assertLogs("repo_wiki", level="INFO") as logs:
            result = IngestionService(strict_settings, strict_store).ingest_local(
                malicious,
                license_policy="permissive_only",
            )
            RetrievalService(strict_store).retrieve("secret handling", license_policy="permissive_only")

        indexed_paths = {file.path for file in result.files}
        self.assertNotIn(".env", indexed_paths)
        self.assertNotIn("binary.py", indexed_paths)
        self.assertNotIn("large.py", indexed_paths)
        self.assertNotIn("outside_link.py", indexed_paths)
        self.assertEqual(result.repository.license, "GPL")
        self.assertEqual(result.source_refs[0].snippet_allowed, False)
        self.assertIn("[REDACTED_SECRET]", result.files[0].content)
        self.assertNotIn("super-secret-value", result.files[0].content)
        self.assertTrue(any('"event": "ingestion.completed"' in line for line in logs.output))
        self.assertTrue(any('"event": "retrieval.completed"' in line for line in logs.output))

        allow_all = RetrievalService(strict_store).retrieve(
            "handle secret",
            license_policy="allow_all_public",
        )["context_pack"]
        permissive = RetrievalService(strict_store).retrieve(
            "handle secret",
            license_policy="permissive_only",
        )["context_pack"]
        self.assertTrue(allow_all["source_citations"])
        self.assertEqual(permissive["source_citations"], [])

        backup_path = self.root / "backup" / "repo-wiki.sqlite"
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main_with_data_dir(strict_settings.data_dir, ["backup", "create", str(backup_path)]), 0)
        self.assertTrue(backup_path.exists())
        self.assertIn("backup", output.getvalue())

        restored_store = SQLiteStore(self.root / "restored" / "repo-wiki.db")
        restored_store.initialize()
        restored_store.restore_from(backup_path)
        self.assertEqual(
            MetricsService(restored_store).metrics()["indexed_repositories"],
            MetricsService(strict_store).metrics()["indexed_repositories"],
        )

        body = json.dumps({"path": str(self.root / "missing")}).encode("utf-8")
        handler = object.__new__(http.RepoWikiHandler)
        handler.store_ref = self.store
        handler.settings_ref = self.settings
        handler.path = "/v1/ingest/local"
        handler.headers = {"Content-Length": str(len(body))}
        handler.rfile = io.BytesIO(body)
        handler.wfile = io.BytesIO()
        handler.send_response = lambda status: setattr(handler, "status", status)
        handler.send_header = lambda *args: None
        handler.end_headers = lambda: None
        http.RepoWikiHandler.do_POST(handler)
        self.assertEqual(handler.status, 404)
        self.assertEqual(json.loads(handler.wfile.getvalue())["error"]["type"], "RepositoryNotFound")

        mcp_error = handle_json_rpc(
            {
                "jsonrpc": "2.0",
                "id": 42,
                "method": "tools/call",
                "params": {"name": "inspect_repository", "arguments": {"repo_id": "missing"}},
            },
            self.store,
        )
        self.assertEqual(mcp_error["id"], 42)
        self.assertEqual(mcp_error["error"]["data"]["type"], "RepositoryNotFound")

        old_data_dir = os.environ.get("REPO_WIKI_DATA_DIR")
        os.environ["REPO_WIKI_DATA_DIR"] = str(strict_settings.data_dir)
        try:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["doctor"]), 0)
            doctor = output.getvalue()
        finally:
            if old_data_dir is None:
                os.environ.pop("REPO_WIKI_DATA_DIR", None)
            else:
                os.environ["REPO_WIKI_DATA_DIR"] = old_data_dir
        self.assertIn("schema version", doctor)
        self.assertIn("config load", doctor)
        self.assertIn("optional FastAPI", doctor)

    def test_phase7_release_docs_and_verification_contract(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        readme = (project_root / "README.md").read_text(encoding="utf-8")
        testing = (project_root / "docs" / "development" / "testing.md").read_text(
            encoding="utf-8"
        )
        benchmark = (project_root / "docs" / "benchmarks" / "mvp-results.md").read_text(
            encoding="utf-8"
        )
        retrieval_quality = (
            project_root / "docs" / "benchmarks" / "retrieval-quality.md"
        ).read_text(encoding="utf-8")
        pyproject = (project_root / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('"dataset/graphrag-main"', pyproject)
        self.assertIn("python3 -m pip install -e .", readme)
        self.assertIn("python3 -m ruff check .", readme)
        self.assertIn("python3 -m repo_wiki.interfaces.cli api serve", readme)
        self.assertIn("python3 -m repo_wiki.interfaces.cli mcp serve", readme)
        self.assertIn("python3 -m repo_wiki.interfaces.cli benchmark report", readme)
        self.assertIn("docs/benchmarks/retrieval-quality.md", readme)
        self.assertIn("Release checks", testing)
        self.assertIn("python -m compileall repo_wiki", testing)
        self.assertIn("python -m ruff check .", testing)
        self.assertIn("Retrieval Quality Suite", benchmark)
        self.assertIn("Average latency", benchmark)
        self.assertIn("Candidate Counts", benchmark)
        self.assertIn("GraphRAG-style config validation", retrieval_quality)
        self.assertIn("FastAPI config endpoint validation", retrieval_quality)
        self.assertIn("Parser behavior and same-stem tests", retrieval_quality)

    def test_phase8_release_docs_and_final_gate_are_recorded(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        readme = (project_root / "README.md").read_text(encoding="utf-8")
        changelog = (project_root / "CHANGELOG.md").read_text(encoding="utf-8")
        release = (project_root / "docs" / "release" / "v0.1.0.md").read_text(
            encoding="utf-8"
        )
        mcp_setup = (project_root / "docs" / "usage" / "mcp-setup.md").read_text(
            encoding="utf-8"
        )
        mcp_examples = (project_root / "docs" / "examples" / "mcp.md").read_text(
            encoding="utf-8"
        )
        benchmark = (project_root / "docs" / "benchmarks" / "mvp-results.md").read_text(
            encoding="utf-8"
        )
        progress = (project_root / "progress.md").read_text(encoding="utf-8")

        self.assertIn("## v0.1.0", changelog)
        self.assertIn("Release recommendation", release)
        self.assertIn("context_pack.v1", readme)
        self.assertIn('"command": "repo-wiki"', mcp_setup)
        self.assertIn('"schema_version": "context_pack.v1"', mcp_examples)
        self.assertIn("Per-Category Quality", benchmark)
        self.assertIn("[██████████] 100%", progress)
        self.assertIn("Phase 9: Final Production Gate", progress)

def main_with_data_dir(data_dir: Path, argv: list[str]) -> int:
    old_data_dir = os.environ.get("REPO_WIKI_DATA_DIR")
    os.environ["REPO_WIKI_DATA_DIR"] = str(data_dir)
    try:
        return main(argv)
    finally:
        if old_data_dir is None:
            os.environ.pop("REPO_WIKI_DATA_DIR", None)
        else:
            os.environ["REPO_WIKI_DATA_DIR"] = old_data_dir


if __name__ == "__main__":
    unittest.main()
