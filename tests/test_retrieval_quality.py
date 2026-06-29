from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_wiki.benchmarks.report import build_benchmark_report
from repo_wiki.benchmarks.retrieval_cases import RETRIEVAL_QUALITY_CASES
from repo_wiki.benchmarks.retrieval_cases import retrieval_case
from repo_wiki.compile.generator import infer_domain
from repo_wiki.config import Settings
from repo_wiki.core.ingestion_service import IngestionService
from repo_wiki.core.retrieval_service import normalized_terms
from repo_wiki.core.retrieval_service import RetrievalService
from repo_wiki.retrieval.classifier import infer_domain as infer_retrieval_domain
from repo_wiki.storage.sqlite import SQLiteStore


class RetrievalQualityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
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

    def test_normalized_terms_split_code_paths_and_snake_case(self) -> None:
        terms = normalized_terms("packages/graphrag/graphrag/query/context_builder.py")

        self.assertIn("query", terms)
        self.assertIn("context", terms)
        self.assertIn("builder", terms)

    def test_repo_scoped_retrieval_returns_only_requested_repo_citations(self) -> None:
        repo_a = self._write_repo("repo-a", "def build_query_context():\n    return 'alpha'\n")
        repo_b = self._write_repo("repo-b", "def build_query_context():\n    return 'beta'\n")
        result_a = IngestionService(self.settings, self.store).ingest_local(repo_a)
        IngestionService(self.settings, self.store).ingest_local(repo_b)

        pack = RetrievalService(self.store).retrieve(
            "how does GraphRAG build query context",
            repo=result_a.repository.id,
            limit=5,
        )["context_pack"]

        returned_citations = [
            citation
            for section in (
                pack["recommended_patterns"],
                pack["relevant_examples"],
                pack["architecture_rules"],
            )
            for item in section
            for citation in item["citations"]
        ]
        self.assertTrue(returned_citations)
        self.assertEqual(
            {result_a.repository.id},
            {citation["repo_id"] for citation in returned_citations},
        )
        self.assertEqual(
            {result_a.repository.id},
            {c["repo_id"] for c in pack["source_citations"]},
        )
        self.assertEqual(result_a.repository.id, pack["constraints"]["repo"])
        self.assertEqual(pack["schema_version"], "context_pack.v1")

    def test_graphrag_query_context_expected_files_are_top_ranked(self) -> None:
        repo = self._write_repo("graphrag", "def build_query_context():\n    return 'context'\n")
        package_dir = repo / "packages" / "graphrag" / "query"
        (package_dir / "api.py").write_text(
            "def query():\n    return build_response()\n",
            encoding="utf-8",
        )
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        pack = RetrievalService(self.store).retrieve(
            "how does GraphRAG build query context",
            repo=result.repository.id,
            limit=3,
        )["context_pack"]

        top_paths = [
            item["citations"][0]["path"]
            for item in pack["recommended_patterns"]
            if item["citations"]
        ]
        self.assertIn("packages/graphrag/query/context_builder.py", top_paths[:2])

    def test_query_context_path_terms_outrank_other_context_builders(self) -> None:
        repo = self._write_repo("graphrag", "def build_query_context():\n    return 'query'\n")
        query_dir = repo / "packages" / "graphrag" / "query" / "context_builder"
        query_dir.mkdir(parents=True)
        (query_dir / "__init__.py").write_text("", encoding="utf-8")
        (query_dir / "builders.py").write_text(
            "def build_query_context():\n    return 'query'\n",
            encoding="utf-8",
        )
        other_dir = repo / "packages" / "graphrag" / "index" / "operations" / "graph_context"
        other_dir.mkdir(parents=True)
        (other_dir / "context_builder.py").write_text(
            "def build_context():\n    return 'graph'\n",
            encoding="utf-8",
        )
        (other_dir / "sort_context.py").write_text(
            "def sort_context():\n    return []\n",
            encoding="utf-8",
        )
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        pack = RetrievalService(self.store).retrieve(
            "how does GraphRAG build query context",
            repo=result.repository.id,
            limit=3,
        )["context_pack"]

        self.assertIn(
            "packages/graphrag/query/context_builder",
            pack["recommended_patterns"][0]["summary"],
        )

    def test_code_modification_task_promotes_exact_source_and_related_tests(self) -> None:
        case = retrieval_case("graphrag_config_validation")
        repo = self.root / "graphrag"
        repo.mkdir()
        (repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        chunking_dir = repo / "packages" / "graphrag-chunking" / "graphrag_chunking"
        chunking_dir.mkdir(parents=True)
        (chunking_dir / "chunking_config.py").write_text(
            "from pydantic import BaseModel\n\n"
            "class ChunkingConfig(BaseModel):\n"
            "    size: int = 1200\n"
            "    overlap: int = 100\n",
            encoding="utf-8",
        )
        (chunking_dir / "token_chunker.py").write_text(
            "def split_text_on_tokens(text, chunk_size, chunk_overlap):\n"
            "    start_idx = 0\n"
            "    start_idx += chunk_size - chunk_overlap\n"
            "    return [text]\n",
            encoding="utf-8",
        )
        for name in (
            "__init__",
            "bootstrap_nltk",
            "chunker",
            "chunk_strategy_type",
            "sentence_chunker",
            "transformers",
        ):
            (chunking_dir / f"{name}.py").write_text(
                f"def {name}_helper():\n    return '{name}'\n",
                encoding="utf-8",
            )
        tests_dir = repo / "tests" / "unit" / "chunking"
        tests_dir.mkdir(parents=True)
        (tests_dir / "test_chunker.py").write_text(
            "from graphrag_chunking.chunking_config import ChunkingConfig\n\n"
            "def test_chunking_config_validation():\n"
            "    assert ChunkingConfig(size=10, overlap=1)\n",
            encoding="utf-8",
        )
        config_tests_dir = repo / "tests" / "unit" / "config"
        config_tests_dir.mkdir(parents=True)
        (config_tests_dir / "test_rate_limit_config.py").write_text(
            "from pydantic import BaseModel, field_validator\n\n"
            "class RateLimitConfig(BaseModel):\n"
            "    requests_per_minute: int\n\n"
            "    @field_validator('requests_per_minute')\n"
            "    @classmethod\n"
            "    def validate_positive(cls, value):\n"
            "        if value <= 0:\n"
            "            raise ValueError('requests_per_minute must be positive')\n"
            "        return value\n\n"
            "def test_rate_limit_config_rejects_non_positive_values():\n"
            "    assert RateLimitConfig(requests_per_minute=10)\n",
            encoding="utf-8",
        )
        (config_tests_dir / "utils.py").write_text(
            "def assert_config_validation_error(config_factory):\n"
            "    return config_factory\n",
            encoding="utf-8",
        )
        indexing_tests_dir = repo / "tests" / "unit" / "indexing"
        indexing_tests_dir.mkdir(parents=True)
        (indexing_tests_dir / "test_profiling.py").write_text(
            "def test_indexing_profile_records_config_size_overlap_metrics():\n"
            "    assert {'config': True, 'size': 1, 'overlap': 0}\n",
            encoding="utf-8",
        )
        (indexing_tests_dir / "test_init_content.py").write_text(
            "def test_init_content_uses_default_token_config():\n"
            "    assert 'token config'\n",
            encoding="utf-8",
        )
        github_dir = repo / ".github" / "workflows"
        github_dir.mkdir(parents=True)
        (github_dir / "gh-pages.yml").write_text(
            "name: gh-pages\nenv:\n  PYTHON_VERSION: '3.12'\n",
            encoding="utf-8",
        )
        storage_dir = repo / "packages" / "graphrag-storage" / "graphrag_storage"
        storage_dir.mkdir(parents=True)
        (storage_dir / "azure_blob_storage.py").write_text(
            "\n".join(
                [
                    "class AzureBlobStorage:",
                    "    def __init__(self): pass",
                    "    def connect(self): pass",
                    "    def load(self): pass",
                    "    def save(self): pass",
                ]
            ),
            encoding="utf-8",
        )
        vector_dir = repo / "packages" / "graphrag-vectors" / "graphrag_vectors"
        vector_dir.mkdir(parents=True)
        (vector_dir / "cosmosdb.py").write_text(
            "\n".join(
                [
                    "class CosmosDBVectorStore:",
                    "    def __init__(self): pass",
                    "    def connect(self): pass",
                    "    def create_database(self): pass",
                    "    def search(self): pass",
                ]
            ),
            encoding="utf-8",
        )
        config_model_dir = repo / "packages" / "graphrag" / "graphrag" / "config" / "models"
        config_model_dir.mkdir(parents=True)
        (config_model_dir / "graph_rag_config.py").write_text(
            "class GraphRagConfig:\n"
            "    chunking_config = None\n"
            "    def model_validate(self): return self\n",
            encoding="utf-8",
        )
        config_dir = repo / "packages" / "graphrag" / "graphrag" / "config"
        (config_dir / "init_content.py").write_text(
            "INIT_YAML = 'chunking config size overlap token defaults'\n",
            encoding="utf-8",
        )
        for index in range(14):
            generic_dir = repo / "packages" / f"generic-{index}" / f"generic_{index}"
            generic_dir.mkdir(parents=True)
            methods = "\n".join(
                f"    def method_{method}(self): return {method}" for method in range(12)
            )
            (generic_dir / "service.py").write_text(
                f"class GenericService{index}:\n{methods}\n",
                encoding="utf-8",
            )
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        pack = RetrievalService(self.store).retrieve(
            case.query,
            repo=result.repository.id,
            language="Python",
            limit=5,
        )
        trace = self.store.get_retrieval_trace(pack["trace_id"])
        context_pack = pack["context_pack"]
        self.assertGreaterEqual(trace["latency_ms"], 0)
        self.assertTrue(context_pack["source_citations"])

        paths = [
            citation["path"]
            for section in (
                context_pack["recommended_patterns"],
                context_pack["relevant_examples"],
                context_pack["architecture_rules"],
            )
            for item in section
            for citation in item["citations"]
        ]
        paths.extend(citation["path"] for citation in context_pack["source_citations"])
        top_paths = paths[:5]
        ranked_paths = [
            item.get("path")
            for item in trace["payload"]["ranking_details"][:5]
        ]
        all_ranked_paths = [
            item.get("path")
            for item in trace["payload"]["ranking_details"]
        ]
        chunking_config_path = case.expected_roles["primary_edit_target"]
        token_chunker_path = case.expected_roles["runtime_risk"]
        test_chunker_path = case.expected_roles["related_test"]

        self.assertIn(chunking_config_path, top_paths)
        self.assertIn(chunking_config_path, ranked_paths[:2])
        self.assertIn(token_chunker_path, ranked_paths[:4])
        self.assertIn(test_chunker_path, ranked_paths[:4])
        for weak_test_path in (
            "tests/unit/config/utils.py",
            "tests/unit/indexing/test_profiling.py",
            "tests/unit/indexing/test_init_content.py",
        ):
            if weak_test_path in all_ranked_paths:
                weak_rank = all_ranked_paths.index(weak_test_path)
                self.assertFalse(
                    weak_rank < all_ranked_paths.index(token_chunker_path)
                    and weak_rank < all_ranked_paths.index(test_chunker_path)
                )
        self.assertNotIn(".github/workflows/gh-pages.yml", top_paths)
        self.assertLessEqual(paths[:8].count("packages/graphrag-storage/graphrag_storage/azure_blob_storage.py"), 1)
        self.assertIn(
            "symbol match",
            " ".join(context_pack["recommended_patterns"][0]["why_relevant"]),
        )
        context_markdown = pack["markdown"].lower()
        self.assertIn("validation boundary", context_markdown)
        self.assertIn("runtime risk", context_markdown)
        self.assertIn("best local unit test", context_markdown)
        self.assertNotIn(
            "tests/unit/config/utils.py as the best local unit test",
            context_markdown,
        )
        self.assertNotIn(
            "tests/unit/indexing/test_profiling.py as the best local unit test",
            context_markdown,
        )
        self.assertNotIn(
            "tests/unit/indexing/test_init_content.py as the best local unit test",
            context_markdown,
        )

    def test_fastapi_config_validation_task_promotes_api_target_tests_and_risk(self) -> None:
        case = retrieval_case("fastapi_config_endpoint_validation")
        repo = self.root / "fastapi-config"
        repo.mkdir()
        (repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        (repo / "requirements.txt").write_text("fastapi>=0.100\npytest>=8\n", encoding="utf-8")
        api_dir = repo / "server" / "api" / "config"
        api_dir.mkdir(parents=True)
        (api_dir / "__init__.py").write_text(
            "from fastapi import APIRouter\n"
            "from .global_config import router as global_router\n"
            "from .mcp import router as mcp_router\n"
            "from .models import router as models_router\n"
            "from .validation import router as validation_router\n\n"
            "router = APIRouter()\n"
            "router.include_router(global_router)\n"
            "router.include_router(models_router)\n"
            "router.include_router(validation_router)\n"
            "router.include_router(mcp_router)\n",
            encoding="utf-8",
        )
        (api_dir / "mcp.py").write_text(
            "from fastapi import APIRouter, HTTPException\n"
            "from pydantic import BaseModel\n"
            "from server.database.config.mcp_manager import mcp_config_manager\n\n"
            "router = APIRouter()\n\n"
            "class McpServerCreate(BaseModel):\n"
            "    name: str\n"
            "    url: str\n"
            "    allow_sensitive_data: bool = False\n\n"
            "class McpServerUpdate(BaseModel):\n"
            "    name: str | None = None\n"
            "    url: str | None = None\n"
            "    allow_sensitive_data: bool | None = None\n\n"
            "@router.post('/mcp')\n"
            "async def add_mcp_server(data: McpServerCreate):\n"
            "    return mcp_config_manager.add_server(name=data.name, url=data.url)\n\n"
            "@router.put('/mcp/{server_id}')\n"
            "async def update_mcp_server(server_id: int, data: McpServerUpdate):\n"
            "    server = mcp_config_manager.update_server(server_id, name=data.name, url=data.url)\n"
            "    if not server:\n"
            "        raise HTTPException(status_code=404, detail='not found')\n"
            "    return server\n",
            encoding="utf-8",
        )
        (api_dir / "validation.py").write_text(
            "from fastapi import APIRouter, HTTPException, Query\n"
            "from server.utils.url_utils import build_openai_v1_url\n\n"
            "router = APIRouter()\n\n"
            "def _normalize_validation_type(request_type: str) -> str:\n"
            "    normalized = request_type.lower().strip()\n"
            "    if normalized in {'openai', 'whisper'}:\n"
            "        return normalized\n"
            "    raise HTTPException(status_code=400, detail='Invalid URL type')\n\n"
            "@router.get('/validate-url')\n"
            "async def validate_url(url: str = Query(...), type: str = Query(...)):\n"
            "    return {'url': build_openai_v1_url(url, 'models')}\n",
            encoding="utf-8",
        )
        for name in ("global_config", "models"):
            (api_dir / f"{name}.py").write_text(
                "from fastapi import APIRouter\n\n"
                "router = APIRouter()\n\n"
                "def update_config():\n"
                "    return {'config': True}\n",
                encoding="utf-8",
            )
        manager_dir = repo / "server" / "database" / "config"
        manager_dir.mkdir(parents=True)
        (manager_dir / "mcp_manager.py").write_text(
            "class McpConfigManager:\n"
            "    def get_servers(self):\n"
            "        return []\n"
            "    def add_server(self, name: str, url: str):\n"
            "        return {'name': name, 'url': url}\n"
            "    def update_server(self, server_id: int, name: str | None = None, url: str | None = None):\n"
            "        return {'id': server_id, 'name': name, 'url': url}\n\n"
            "mcp_config_manager = McpConfigManager()\n",
            encoding="utf-8",
        )
        (manager_dir / "manager.py").write_text(
            "class ConfigManager:\n"
            "    def update_config(self, data):\n"
            "        return data\n",
            encoding="utf-8",
        )
        utils_dir = repo / "server" / "utils"
        (utils_dir / "mcp").mkdir(parents=True)
        (utils_dir / "mcp" / "client.py").write_text(
            "class McpServerClient:\n"
            "    def __init__(self, server_config):\n"
            "        self.server_config = server_config\n"
            "    async def connect(self):\n"
            "        url = self.server_config.get('url')\n"
            "        if not url:\n"
            "            return False\n"
            "        return True\n",
            encoding="utf-8",
        )
        (utils_dir / "url_utils.py").write_text(
            "from urllib.parse import urlsplit\n\n"
            "def build_openai_v1_url(base_url: str, endpoint_path: str) -> str:\n"
            "    parts = urlsplit(base_url.strip())\n"
            "    if not parts.scheme or not parts.netloc:\n"
            "        raise ValueError('invalid URL')\n"
            "    return base_url.rstrip('/') + '/v1/' + endpoint_path.lstrip('/')\n",
            encoding="utf-8",
        )
        chat_tools_dir = repo / "server" / "utils" / "chat" / "tools"
        chat_tools_dir.mkdir(parents=True)
        (chat_tools_dir / "registry.py").write_text(
            "def get_tools_definition(config_manager):\n"
            "    return {'config': config_manager}\n",
            encoding="utf-8",
        )
        api_root = repo / "server" / "api"
        (api_root / "chat.py").write_text(
            "from fastapi import APIRouter\n\n"
            "router = APIRouter()\n\n"
            "@router.post('/chat')\n"
            "async def chat_endpoint(payload: dict):\n"
            "    return {'message': payload.get('message')}\n",
            encoding="utf-8",
        )
        tests_dir = repo / "server" / "tests"
        tests_dir.mkdir(parents=True)
        (tests_dir / "test_config.py").write_text(
            "from fastapi.testclient import TestClient\n"
            "from server.api.config import router\n\n"
            "def test_add_mcp_server_endpoint():\n"
            "    assert router\n",
            encoding="utf-8",
        )
        (tests_dir / "test_chat.py").write_text(
            "from server.api.chat import router\n\n"
            "def test_chat_endpoint():\n"
            "    assert router\n",
            encoding="utf-8",
        )
        (tests_dir / "test_database.py").write_text(
            "def test_database_tables_exist():\n"
            "    assert 'mcp_servers'\n",
            encoding="utf-8",
        )
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        pack = RetrievalService(self.store).retrieve(
            case.query,
            repo=result.repository.id,
            language="Python",
            framework="FastAPI",
            domain="configuration",
            limit=10,
        )
        trace = self.store.get_retrieval_trace(pack["trace_id"])
        context_pack = pack["context_pack"]
        self.assertGreaterEqual(trace["latency_ms"], 0)
        self.assertTrue(context_pack["source_citations"])
        ranked_paths = [
            item.get("path")
            for item in trace["payload"]["ranking_details"]
        ]

        api_path = case.expected_roles["primary_edit_target"]
        manager_path = case.expected_roles["runtime_persistence_boundary"]
        test_path = case.expected_roles["related_test"]
        validation_path = case.expected_roles["convention_example"]
        client_path = case.expected_roles["runtime_consequence"]
        noisy_path = "server/utils/chat/tools/registry.py"
        noisy_test_path = "server/tests/test_chat.py"
        noisy_database_test_path = "server/tests/test_database.py"

        self.assertIn(api_path, ranked_paths[:3])
        self.assertIn(test_path, ranked_paths[:5])
        self.assertIn(manager_path, ranked_paths[:5])
        self.assertLess(ranked_paths.index(api_path), ranked_paths.index(client_path))
        if noisy_path in ranked_paths:
            self.assertGreater(ranked_paths.index(noisy_path), ranked_paths.index(api_path))
        if noisy_test_path in ranked_paths:
            self.assertGreater(ranked_paths.index(noisy_test_path), ranked_paths.index(test_path))
        if noisy_database_test_path in ranked_paths:
            self.assertGreater(
                ranked_paths.index(noisy_database_test_path),
                ranked_paths.index(test_path),
            )
        self.assertIn(validation_path, ranked_paths[:8])

        markdown = pack["markdown"].lower()
        self.assertIn("edit target", markdown)
        self.assertIn("runtime risk", markdown)
        self.assertIn("best local unit test", markdown)
        self.assertIn("validation convention", markdown)
        self.assertIn(api_path, markdown)
        self.assertIn(test_path, markdown)
        self.assertNotIn(f"{noisy_test_path} as the best local unit test", markdown)
        self.assertNotIn(
            f"{noisy_database_test_path} as the best local unit test",
            markdown,
        )
        tests_to_consider = context_pack["tests_to_consider"]
        self.assertFalse(any(noisy_test_path in item for item in tests_to_consider))
        self.assertFalse(any(noisy_database_test_path in item for item in tests_to_consider))

    def test_parser_task_pairs_same_stem_test_and_reports_edge_cases(self) -> None:
        case = retrieval_case("dotenv_parser_same_stem")
        repo = self.root / "dotenv-like"
        repo.mkdir()
        (repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        source_dir = repo / "src" / "dotenv"
        source_dir.mkdir(parents=True)
        tests_dir = repo / "tests"
        tests_dir.mkdir()
        (source_dir / "parser.py").write_text(
            "import re\n\n"
            "_unquoted_value = re.compile(r'([^\\r\\n]*)')\n"
            "_comment = re.compile(r'(?:[^\\S\\r\\n]*#[^\\r\\n]*)?')\n\n"
            "def parse_unquoted_value(reader):\n"
            "    part = reader.read_regex(_unquoted_value)[0]\n"
            "    return re.sub(r'\\s+#.*', '', part).rstrip()\n\n"
            "def parse_stream(stream):\n"
            "    return stream.read()\n",
            encoding="utf-8",
        )
        (source_dir / "main.py").write_text(
            "from .parser import parse_stream\n\n"
            "class DotEnv:\n"
            "    def parse(self, stream):\n"
            "        return parse_stream(stream)\n",
            encoding="utf-8",
        )
        (source_dir / "variables.py").write_text(
            "class Literal:\n"
            "    def __init__(self, value):\n"
            "        self.value = value\n\n"
            "def parse_variables(value):\n"
            "    return [Literal(value)]\n",
            encoding="utf-8",
        )
        (tests_dir / "test_parser.py").write_text(
            "import pytest\n\n"
            "@pytest.mark.parametrize('source, expected', [\n"
            "    ('a=b#c', 'b#c'),\n"
            "    ('a=b #c', 'b'),\n"
            "    ('a=b\\t#c', 'b'),\n"
            "])\n"
            "def test_parse_stream(source, expected):\n"
            "    assert expected\n",
            encoding="utf-8",
        )
        (tests_dir / "test_variables.py").write_text(
            "from dotenv.variables import parse_variables\n\n"
            "def test_parse_variables_literal_value():\n"
            "    assert parse_variables('literal value')\n",
            encoding="utf-8",
        )
        for name in ("test_zip_imports", "test_cli", "test_utils"):
            (tests_dir / f"{name}.py").write_text(
                "def test_general_behavior():\n"
                "    assert 'dotenv value tests'\n",
                encoding="utf-8",
            )
        result = IngestionService(self.settings, self.store).ingest_local(
            repo,
            license_policy="metadata_only",
        )

        pack = RetrievalService(self.store).retrieve(
            case.query,
            repo=result.repository.id,
            language="Python",
            framework="pytest",
            domain="parser-config",
            limit=10,
        )
        trace = self.store.get_retrieval_trace(pack["trace_id"])
        context_pack = pack["context_pack"]
        self.assertGreaterEqual(trace["latency_ms"], 0)
        ranked_paths = [
            item.get("path")
            for item in trace["payload"]["ranking_details"]
        ]

        parser_path = case.expected_roles["primary_edit_target"]
        main_path = case.expected_roles["runtime_use_site"]
        parser_test_path = case.expected_roles["related_test"]
        noisy_paths = (
            "tests/test_variables.py",
            "tests/test_zip_imports.py",
            "tests/test_cli.py",
            "tests/test_utils.py",
        )

        self.assertIn(parser_path, ranked_paths[:2])
        self.assertIn(parser_test_path, ranked_paths[:3])
        self.assertIn(main_path, ranked_paths[:5])
        for noisy_path in noisy_paths:
            if noisy_path in ranked_paths:
                self.assertGreater(ranked_paths.index(noisy_path), ranked_paths.index(parser_test_path))
        self.assertTrue(context_pack["source_citations"])

        risk_text = " ".join(context_pack["risks"]).lower()
        self.assertTrue(
            any(cue in risk_text for cue in ("literal #", "\\#", "escaped hash", "whitespace"))
        )

    def test_golden_direct_questions_return_expected_paths_and_answer_terms(self) -> None:
        repo = self.root / "golden"
        repo.mkdir()
        (repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        auth_dir = repo / "app" / "api"
        auth_dir.mkdir(parents=True)
        (auth_dir / "auth.ts").write_text(
            "\n".join(
                [
                    "export function auth() {",
                    "  const accessCode = 'code';",
                    "  const apiKey = 'key';",
                    "  const systemApiKey = apiKey;",
                    "  return { accessCode, apiKey, systemApiKey };",
                    "}",
                ]
            ),
            encoding="utf-8",
        )
        (auth_dir / "provider.ts").write_text(
            "export function provider() {\n  return 'provider';\n}\n",
            encoding="utf-8",
        )
        (repo / "app" / "locales").mkdir(parents=True)
        (repo / "app" / "locales" / "cn.ts").write_text(
            "export const auth = 'generic locale auth text';\n", encoding="utf-8"
        )
        inference_dir = repo / "inference"
        inference_dir.mkdir()
        (inference_dir / "model.py").write_text(
            "class ModelArgs:\n"
            "    pass\n\n"
            "class Transformer:\n"
            "    def __init__(self, args: ModelArgs):\n"
            "        self.args = args\n",
            encoding="utf-8",
        )
        (inference_dir / "generate.py").write_text(
            "import json\nfrom .model import ModelArgs, Transformer\n\n"
            "def load_config(path):\n"
            "    with open(path) as f:\n"
            "        args = ModelArgs(**json.load(f))\n"
            "    return Transformer(args)\n",
            encoding="utf-8",
        )
        result = IngestionService(self.settings, self.store).ingest_local(repo)
        cases = [
            {
                "query": "What does app/api/auth.ts do?",
                "language": "TypeScript",
                "framework": "Next.js",
                "expected_paths": ["app/api/auth.ts"],
                "expected_answer_terms": ["access", "api key", "system api key"],
            },
            {
                "query": "Where is the inference config JSON loaded and who consumes ModelArgs?",
                "language": "Python",
                "framework": None,
                "expected_paths": ["inference/generate.py", "inference/model.py"],
                "expected_answer_terms": ["json", "ModelArgs", "Transformer"],
            },
        ]

        for case in cases:
            with self.subTest(case["query"]):
                pack = RetrievalService(self.store).retrieve(
                    case["query"],
                    repo=result.repository.id,
                    language=case["language"],
                    framework=case["framework"],
                    limit=5,
                )["context_pack"]

                paths = []
                for item in pack["recommended_patterns"][:5]:
                    if item["citations"]:
                        paths.append(item["citations"][0]["path"])
                paths.extend(citation["path"] for citation in pack["source_citations"][:5])
                for expected_path in case["expected_paths"]:
                    self.assertIn(expected_path, paths)
                if case["query"] == "What does app/api/auth.ts do?":
                    self.assertEqual("app/api/auth.ts", paths[0])
                answer = pack["answer"].lower()
                for term in case["expected_answer_terms"]:
                    self.assertIn(term.lower(), answer)

    def test_model_path_alone_is_not_database_domain(self) -> None:
        self.assertEqual(infer_domain("inference/model.py", set()), "general")
        self.assertEqual(infer_domain("prisma/schema.prisma", set()), "database")
        self.assertIsNone(
            infer_retrieval_domain("What does ModelArgs configure in inference/model.py?")
        )
        self.assertEqual(infer_retrieval_domain("change database schema"), "database")

    def test_benchmark_reports_expected_hits_for_graphrag_context_task(self) -> None:
        repo = self._write_repo("graphrag", "def build_query_context():\n    return 'context'\n")
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        markdown, metrics = build_benchmark_report(
            self.store,
            tasks=("how does GraphRAG build query context",),
            expected_paths={
                "how does GraphRAG build query context": (
                    "packages/graphrag/query/context_builder.py",
                )
            },
            repo=result.repository.id,
        )

        self.assertEqual(1, metrics["expected_hit_count"])
        self.assertEqual(1.0, metrics["top_k_precision"])
        self.assertIn("Expected Hits", markdown)
        self.assertIn("1/1", markdown)

    def test_benchmark_report_says_expected_hits_not_configured(self) -> None:
        repo = self._write_repo("graphrag", "def build_query_context():\n    return 'context'\n")
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        markdown, metrics = build_benchmark_report(
            self.store,
            tasks=("how does GraphRAG build query context",),
            repo=result.repository.id,
        )

        self.assertEqual(0, metrics["expected_total"])
        self.assertIn("Expected Hits", markdown)
        self.assertIn("not configured", markdown)
        self.assertNotIn("0/0", markdown)

    def test_benchmark_report_groups_quality_by_task_category(self) -> None:
        repo = self._write_repo("graphrag", "def build_query_context():\n    return 'context'\n")
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        markdown, metrics = build_benchmark_report(
            self.store,
            tasks=(
                "backend: how does GraphRAG build query context",
                "testing: how does GraphRAG build query context",
            ),
            expected_paths={
                "backend: how does GraphRAG build query context": (
                    "packages/graphrag/query/context_builder.py",
                ),
                "testing: how does GraphRAG build query context": (
                    "packages/graphrag/query/context_builder.py",
                ),
            },
            repo=result.repository.id,
        )

        self.assertIn("per_category", metrics)
        self.assertEqual(1.0, metrics["per_category"]["backend"]["top_k_precision"])
        self.assertEqual(1.0, metrics["per_category"]["testing"]["top_k_precision"])
        self.assertIn("## Per-Category Quality", markdown)
        self.assertIn("| backend |", markdown)

    def test_retrieval_quality_benchmark_cases_are_documented(self) -> None:
        case_ids = {case.id for case in RETRIEVAL_QUALITY_CASES}

        self.assertEqual(
            {
                "graphrag_config_validation",
                "fastapi_config_endpoint_validation",
                "dotenv_parser_same_stem",
            },
            case_ids,
        )
        for case in RETRIEVAL_QUALITY_CASES:
            self.assertTrue(case.query)
            self.assertTrue(case.expected_roles)
            self.assertTrue(case.pass_criteria)
            self.assertTrue(case.test_name.startswith("test_"))

    def test_architecture_patterns_include_adrs_and_repeated_modules(self) -> None:
        repo = self._write_repo("patterns", "def build_query_context():\n    return 'context'\n")
        service_dir = repo / "app" / "services"
        service_dir.mkdir(parents=True)
        (service_dir / "auth.py").write_text("def issue_token():\n    return 'token'\n")
        (service_dir / "users.py").write_text("def load_user():\n    return 'user'\n")
        adr_dir = repo / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        (adr_dir / "0001-local-storage.md").write_text(
            "# ADR 0001: Local Storage\n\n## Status\nAccepted\n\n## Decision\nUse SQLite.\n",
            encoding="utf-8",
        )

        result = IngestionService(self.settings, self.store).ingest_local(repo)
        by_type = {obj.type: obj for obj in result.knowledge_objects}

        self.assertIn("DecisionRecord", by_type)
        self.assertIn("ModulePattern", by_type)
        self.assertTrue(by_type["DecisionRecord"].source_refs)
        self.assertGreaterEqual(len(by_type["ModulePattern"].source_refs), 2)

    def test_ab_exact_provider_entity_outranks_generic_provider_config(self) -> None:
        repo = self.root / "openscribe-like"
        repo.mkdir()
        (repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        provider_dir = repo / "packages" / "pipeline" / "src"
        config_dir = repo / "packages" / "config" / "src"
        storage_dir = repo / "packages" / "storage" / "src"
        provider_dir.mkdir(parents=True)
        config_dir.mkdir(parents=True)
        storage_dir.mkdir(parents=True)
        (provider_dir / "provider-resolver.ts").write_text(
            "export const TRANSCRIPTION_PROVIDER = 'transcriptionProvider';\n\n"
            "export function resolveTranscriptionProvider(config: Record<string, string>) {\n"
            "  const provider = config[TRANSCRIPTION_PROVIDER] ?? 'deepgram';\n"
            "  if (!provider.trim()) throw new Error('provider is required');\n"
            "  return provider;\n"
            "}\n",
            encoding="utf-8",
        )
        (provider_dir / "provider-resolver.test.ts").write_text(
            "import { resolveTranscriptionProvider } from './provider-resolver';\n\n"
            "it('rejects a blank transcription provider', () => {\n"
            "  expect(() => resolveTranscriptionProvider({ transcriptionProvider: '' })).toThrow();\n"
            "});\n",
            encoding="utf-8",
        )
        (config_dir / "api-key-config.ts").write_text(
            "export function validateApiKeyConfig(config: Record<string, string>) {\n"
            "  if (!config.apiKey) throw new Error('api key required');\n"
            "  return config.apiKey;\n"
            "}\n",
            encoding="utf-8",
        )
        (storage_dir / "storage-config.ts").write_text(
            "export function resolveStorageProvider(config: Record<string, string>) {\n"
            "  return config.storageProvider ?? 's3';\n"
            "}\n",
            encoding="utf-8",
        )
        (config_dir / "provider-config.ts").write_text(
            "export function loadGenericProviderConfig(config: Record<string, string>) {\n"
            "  return { provider: config.provider, apiKey: config.apiKey, storage: config.storage };\n"
            "}\n",
            encoding="utf-8",
        )
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        pack = RetrievalService(self.store).retrieve(
            "Add validation to resolveTranscriptionProvider so TRANSCRIPTION_PROVIDER rejects blank provider config values",
            repo=result.repository.id,
            language="TypeScript",
            limit=8,
        )
        trace = self.store.get_retrieval_trace(pack["trace_id"])
        context_pack = pack["context_pack"]
        ranked_paths = self._ranked_paths(trace)

        self.assertIn("packages/pipeline/src/provider-resolver.ts", ranked_paths[:2])
        for noisy_path in (
            "packages/config/src/api-key-config.ts",
            "packages/storage/src/storage-config.ts",
            "packages/config/src/provider-config.ts",
        ):
            if noisy_path in ranked_paths:
                self.assertGreater(
                    ranked_paths.index(noisy_path),
                    ranked_paths.index("packages/pipeline/src/provider-resolver.ts"),
                )
            self.assertNotEqual("edit target", self._role_for_path(context_pack, noisy_path))
        self.assertTrue(context_pack["source_citations"])
        self.assertTrue(
            self._citations_for_path(context_pack, "packages/pipeline/src/provider-resolver.ts")
        )

    def test_ab_dapr_runtime_files_are_not_primary_edit_targets(self) -> None:
        repo = self.root / "dapr-like"
        repo.mkdir()
        (repo / "LICENSE").write_text("Apache License\n", encoding="utf-8")
        agents_dir = repo / "dapr_agents" / "agents"
        grpc_dir = repo / "dapr_agents" / "workflow" / "utils"
        types_dir = repo / "dapr_agents" / "types"
        tests_dir = repo / "tests" / "workflow"
        for directory in (agents_dir, grpc_dir, types_dir, tests_dir):
            directory.mkdir(parents=True)
        (agents_dir / "configs.py").write_text(
            "from pydantic import BaseModel\n\n"
            "class WorkflowGrpcOptions(BaseModel):\n"
            "    keepalive_time_ms: int | None = None\n"
            "    keepalive_timeout_ms: int | None = None\n",
            encoding="utf-8",
        )
        (grpc_dir / "grpc.py").write_text(
            "from dapr_agents.agents.configs import WorkflowGrpcOptions\n\n"
            "def apply_grpc_options(options: WorkflowGrpcOptions | None) -> None:\n"
            "    if not options:\n"
            "        return\n"
            "    grpc_options = []\n"
            "    if options.keepalive_time_ms:\n"
            "        grpc_options.append(('grpc.keepalive_time_ms', options.keepalive_time_ms))\n"
            "    if options.keepalive_timeout_ms:\n"
            "        grpc_options.append(('grpc.keepalive_timeout_ms', options.keepalive_timeout_ms))\n",
            encoding="utf-8",
        )
        (types_dir / "workflow.py").write_text(
            "class DaprWorkflowStatus:\n"
            "    RUNNING = 'running'\n"
            "    FAILED = 'failed'\n",
            encoding="utf-8",
        )
        (tests_dir / "test_grpc_options.py").write_text(
            "from dapr_agents.agents.configs import WorkflowGrpcOptions\n\n"
            "def test_workflow_grpc_options_accept_keepalive_values():\n"
            "    assert WorkflowGrpcOptions(keepalive_time_ms=100, keepalive_timeout_ms=10)\n",
            encoding="utf-8",
        )
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        pack = RetrievalService(self.store).retrieve(
            "Add validation for WorkflowGrpcOptions keepalive options so keepalive_timeout_ms cannot be greater than keepalive_time_ms, and add a focused unit test in tests/workflow/test_grpc_options.py.",
            repo=result.repository.id,
            language="Python",
            limit=8,
        )
        context_pack = pack["context_pack"]
        trace = self.store.get_retrieval_trace(pack["trace_id"])
        ranked_paths = self._ranked_paths(trace)

        self.assertIn("dapr_agents/agents/configs.py", ranked_paths[:2])
        self.assertIn("tests/workflow/test_grpc_options.py", ranked_paths[:4])
        self.assertEqual("edit target", self._role_for_path(context_pack, "dapr_agents/agents/configs.py"))
        self.assertNotEqual("edit target", self._role_for_path(context_pack, "dapr_agents/workflow/utils/grpc.py"))
        self.assertNotEqual("edit target", self._role_for_path(context_pack, "dapr_agents/types/workflow.py"))

    def test_ab_provider_resolver_entity_beats_generic_api_storage_error_drift(self) -> None:
        repo = self.root / "openscribe-drift-like"
        repo.mkdir()
        (repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        transcribe_dir = repo / "packages" / "pipeline" / "transcribe" / "src" / "providers"
        shared_dir = repo / "packages" / "pipeline" / "shared" / "src"
        storage_dir = repo / "packages" / "storage" / "src"
        settings_dir = repo / "apps" / "web" / "src" / "app" / "api" / "settings" / "api-keys"
        tests_dir = repo / "packages" / "pipeline" / "transcribe" / "src" / "__tests__"
        for directory in (transcribe_dir, shared_dir, storage_dir, settings_dir, tests_dir):
            directory.mkdir(parents=True)
        (transcribe_dir / "provider-resolver.ts").write_text(
            "export function resolveProvider(provider: string | undefined) {\n"
            "  if (provider === 'medasr' || provider === 'med_asr') return 'medasr';\n"
            "  if (provider === 'whisper_openai' || provider === 'openai') return 'whisper_openai';\n"
            "  return 'whisper_local';\n"
            "}\n",
            encoding="utf-8",
        )
        (tests_dir / "provider-resolver.test.ts").write_text(
            "import { resolveProvider } from '../providers/provider-resolver';\n\n"
            "it('resolves known transcription providers', () => {\n"
            "  expect(resolveProvider('openai')).toBe('whisper_openai');\n"
            "});\n",
            encoding="utf-8",
        )
        (shared_dir / "error-provider.ts").write_text(
            "export function providerError(message: string) {\n"
            "  return new Error(`provider config api key storage error: ${message}`);\n"
            "}\n",
            encoding="utf-8",
        )
        (storage_dir / "server-api-keys.ts").write_text(
            "function getConfigPath() {\n"
            "  return '.api-keys.json';\n"
            "}\n\n"
            "export function getOpenAIApiKey(config: Record<string, string>) {\n"
            "  const key = config.apiKey ?? config.provider ?? config.storage;\n"
            "  if (!key) throw new Error('missing api key provider config');\n"
            "  return `${getConfigPath()}:${key}`;\n"
            "}\n",
            encoding="utf-8",
        )
        (settings_dir / "route.ts").write_text(
            "export async function GET() {\n"
            "  return Response.json({ provider: 'api-key-storage-config' });\n"
            "}\n",
            encoding="utf-8",
        )
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        pack = RetrievalService(self.store).retrieve(
            "Add validation to the transcription provider resolver so unknown TRANSCRIPTION_PROVIDER values throw a clear error instead of silently defaulting to whisper_local, and update packages/pipeline/transcribe/src/__tests__/provider-resolver.test.ts.",
            repo=result.repository.id,
            language="TypeScript",
            framework="Next.js",
            limit=8,
        )
        trace = self.store.get_retrieval_trace(pack["trace_id"])
        context_pack = pack["context_pack"]
        ranked_paths = self._ranked_paths(trace)

        resolver_path = "packages/pipeline/transcribe/src/providers/provider-resolver.ts"
        self.assertIn(resolver_path, ranked_paths[:2])
        self.assertIn("packages/pipeline/transcribe/src/__tests__/provider-resolver.test.ts", ranked_paths[:4])
        for noisy_path in (
            "packages/pipeline/shared/src/error-provider.ts",
            "packages/storage/src/server-api-keys.ts",
            "apps/web/src/app/api/settings/api-keys/route.ts",
        ):
            if noisy_path in ranked_paths:
                self.assertGreater(ranked_paths.index(noisy_path), ranked_paths.index(resolver_path))
            self.assertNotEqual("edit target", self._role_for_path(context_pack, noisy_path))
        self.assertEqual("edit target", self._role_for_path(context_pack, resolver_path))
        self.assertTrue(self._citations_for_path(context_pack, resolver_path))

    def test_ab_exact_parser_entity_outranks_importer_and_html_parser(self) -> None:
        repo = self.root / "openmaic-like"
        repo.mkdir()
        (repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        generation_dir = repo / "lib" / "generation"
        importer_dir = repo / "lib" / "importer"
        utils_dir = repo / "lib" / "utils"
        generation_dir.mkdir(parents=True)
        importer_dir.mkdir(parents=True)
        utils_dir.mkdir(parents=True)
        (generation_dir / "json-repair.ts").write_text(
            "export function parseJsonResponse(text: string) {\n"
            "  const cleaned = text.replace(/^```json/, '').replace(/```$/, '').trim();\n"
            "  return JSON.parse(cleaned);\n"
            "}\n",
            encoding="utf-8",
        )
        (generation_dir / "json-repair.test.ts").write_text(
            "import { parseJsonResponse } from './json-repair';\n\n"
            "it('parses fenced model json responses', () => {\n"
            "  expect(parseJsonResponse('```json\\n{\"ok\":true}\\n```')).toEqual({ ok: true });\n"
            "});\n",
            encoding="utf-8",
        )
        (importer_dir / "parser.ts").write_text(
            "export function parseImporterRows(input: string) {\n"
            "  return input.split('\\n').map((line) => JSON.stringify({ line }));\n"
            "}\n",
            encoding="utf-8",
        )
        (importer_dir / "html-parser.ts").write_text(
            "export function parseHtmlImport(html: string) {\n"
            "  return html.replace(/<[^>]+>/g, '');\n"
            "}\n",
            encoding="utf-8",
        )
        (utils_dir / "json-utils.ts").write_text(
            "export function formatJson(value: unknown) {\n"
            "  return JSON.stringify(value, null, 2);\n"
            "}\n",
            encoding="utf-8",
        )
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        pack = RetrievalService(self.store).retrieve(
            "Fix parseJsonResponse JSON repair behavior for malformed model output and add tests",
            repo=result.repository.id,
            language="TypeScript",
            limit=8,
        )
        trace = self.store.get_retrieval_trace(pack["trace_id"])
        context_pack = pack["context_pack"]
        ranked_paths = self._ranked_paths(trace)

        repair_path = "lib/generation/json-repair.ts"
        test_path = "lib/generation/json-repair.test.ts"
        self.assertIn(repair_path, ranked_paths[:2])
        self.assertIn(test_path, ranked_paths[:5])
        self.assertEqual("edit target", self._role_for_path(context_pack, repair_path))
        for noisy_path in ("lib/importer/parser.ts", "lib/importer/html-parser.ts"):
            if noisy_path in ranked_paths:
                self.assertGreater(ranked_paths.index(noisy_path), ranked_paths.index(repair_path))
        self.assertTrue(context_pack["source_citations"])

    def test_ab_json_repair_path_beats_importer_html_parser_drift_without_symbol(self) -> None:
        repo = self.root / "openmaic-drift-like"
        repo.mkdir()
        (repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        generation_dir = repo / "lib" / "generation"
        importer_dir = repo / "packages" / "@openmaic" / "importer" / "src" / "import-pipeline"
        importer_scripts_dir = repo / "packages" / "@openmaic" / "importer" / "scripts"
        html_dir = repo / "lib" / "export" / "html-parser"
        tests_dir = repo / "tests" / "generation"
        for directory in (generation_dir, importer_dir, importer_scripts_dir, html_dir, tests_dir):
            directory.mkdir(parents=True)
        (generation_dir / "json-repair.ts").write_text(
            "export function repairJsonResponse(text: string) {\n"
            "  return text.replace(/:\\s*\\.(\\d+)/g, ': 0.$1');\n"
            "}\n",
            encoding="utf-8",
        )
        (tests_dir / "json-repair.test.ts").write_text(
            "import { repairJsonResponse } from '../../lib/generation/json-repair';\n\n"
            "it('repairs decimal property fragments', () => {\n"
            "  expect(repairJsonResponse('{\"opacity\": .5}')).toContain('0.5');\n"
            "});\n",
            encoding="utf-8",
        )
        (importer_dir / "index.ts").write_text(
            "export function importPipelineParser(json: string) {\n"
            "  return JSON.parse(json).map((item: unknown) => item);\n"
            "}\n",
            encoding="utf-8",
        )
        (importer_scripts_dir / "transvert.ts").write_text(
            "export function parseImporterJsonFile(json: string) {\n"
            "  return JSON.parse(json);\n"
            "}\n",
            encoding="utf-8",
        )
        (html_dir / "parser.ts").write_text(
            "export function parseHtmlParserJson(html: string) {\n"
            "  return html.replace(/<script type=\"application\\/json\">/g, '');\n"
            "}\n",
            encoding="utf-8",
        )
        (generation_dir / "action-parser.ts").write_text(
            "export function parseActionJson(text: string) {\n"
            "  return JSON.parse(text);\n"
            "}\n",
            encoding="utf-8",
        )
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        pack = RetrievalService(self.store).retrieve(
            'Extend the JSON repair parser to repair quoted numeric property fragments without a leading zero like "opacity: .5" and "x: -.25" without changing valid string content, and add focused tests in tests/generation/json-repair.test.ts.',
            repo=result.repository.id,
            language="TypeScript",
            framework="Next.js",
            limit=10,
        )
        trace = self.store.get_retrieval_trace(pack["trace_id"])
        context_pack = pack["context_pack"]
        ranked_paths = self._ranked_paths(trace)

        repair_path = "lib/generation/json-repair.ts"
        self.assertIn(repair_path, ranked_paths[:2])
        self.assertIn("tests/generation/json-repair.test.ts", ranked_paths[:5])
        self.assertEqual("edit target", self._role_for_path(context_pack, repair_path))
        for noisy_path in (
            "packages/@openmaic/importer/src/import-pipeline/index.ts",
            "packages/@openmaic/importer/scripts/transvert.ts",
            "lib/export/html-parser/parser.ts",
        ):
            if noisy_path in ranked_paths:
                self.assertGreater(ranked_paths.index(noisy_path), ranked_paths.index(repair_path))
            self.assertNotEqual("edit target", self._role_for_path(context_pack, noisy_path))

    def test_ab_typescript_source_pairs_same_stem_test(self) -> None:
        repo = self.root / "voltagent-like"
        repo.mkdir()
        (repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        logger_dir = repo / "packages" / "logger" / "src"
        other_tests = repo / "packages" / "core" / "src"
        logger_dir.mkdir(parents=True)
        other_tests.mkdir(parents=True)
        (logger_dir / "buffer.ts").write_text(
            "export class InMemoryLogBuffer {\n"
            "  private entries: string[] = [];\n"
            "  append(entry: string) { this.entries.push(entry); }\n"
            "  drain() { const entries = this.entries; this.entries = []; return entries; }\n"
            "}\n",
            encoding="utf-8",
        )
        (logger_dir / "buffer.test.ts").write_text(
            "import { InMemoryLogBuffer } from './buffer';\n\n"
            "it('drains buffered entries', () => {\n"
            "  const buffer = new InMemoryLogBuffer();\n"
            "  buffer.append('one');\n"
            "  expect(buffer.drain()).toEqual(['one']);\n"
            "});\n",
            encoding="utf-8",
        )
        (logger_dir / "other.test.ts").write_text(
            "it('covers unrelated logger formatting', () => {\n"
            "  expect('logger output').toContain('logger');\n"
            "});\n",
            encoding="utf-8",
        )
        (other_tests / "buffer.spec.ts").write_text(
            "it('covers unrelated core buffer settings', () => {\n"
            "  expect('core buffer config').toContain('buffer');\n"
            "});\n",
            encoding="utf-8",
        )
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        pack = RetrievalService(self.store).retrieve(
            "Update InMemoryLogBuffer buffer behavior and add a focused TypeScript unit test",
            repo=result.repository.id,
            language="TypeScript",
            limit=8,
        )
        trace = self.store.get_retrieval_trace(pack["trace_id"])
        context_pack = pack["context_pack"]
        ranked_paths = self._ranked_paths(trace)

        source_path = "packages/logger/src/buffer.ts"
        same_stem_test = "packages/logger/src/buffer.test.ts"
        self.assertIn(source_path, ranked_paths[:2])
        self.assertIn(same_stem_test, ranked_paths[:4])
        for noisy_path in ("packages/logger/src/other.test.ts", "packages/core/src/buffer.spec.ts"):
            if noisy_path in ranked_paths:
                self.assertGreater(ranked_paths.index(noisy_path), ranked_paths.index(same_stem_test))
        self.assertTrue(
            self._citations_for_path(context_pack, source_path)
            and self._citations_for_path(context_pack, same_stem_test)
        )

    def test_ab_local_permissive_unknown_license_keeps_file_level_citations(self) -> None:
        repo = self.root / "voltagent-unknown-license-like"
        repo.mkdir()
        logger_dir = repo / "packages" / "logger" / "src"
        logger_dir.mkdir(parents=True)
        (logger_dir / "buffer.ts").write_text(
            "export class InMemoryLogBuffer {\n"
            "  constructor(private maxSize = 100) {}\n"
            "  append(entry: string) { return entry; }\n"
            "}\n",
            encoding="utf-8",
        )
        (logger_dir / "buffer.spec.ts").write_text(
            "import { InMemoryLogBuffer } from './buffer';\n\n"
            "it('constructs the buffer', () => {\n"
            "  expect(new InMemoryLogBuffer()).toBeTruthy();\n"
            "});\n",
            encoding="utf-8",
        )
        result = IngestionService(self.settings, self.store).ingest_local(
            repo,
            license_policy="permissive_only",
        )

        pack = RetrievalService(self.store).retrieve(
            "Add validation to InMemoryLogBuffer so maxSize must be a positive integer, and add focused tests in packages/logger/src/buffer.spec.ts.",
            repo=result.repository.id,
            language="TypeScript",
            limit=8,
            license_policy="permissive_only",
        )
        context_pack = pack["context_pack"]
        trace = self.store.get_retrieval_trace(pack["trace_id"])
        ranked_paths = self._ranked_paths(trace)

        source_path = "packages/logger/src/buffer.ts"
        test_path = "packages/logger/src/buffer.spec.ts"
        self.assertIn(source_path, ranked_paths[:2])
        self.assertIn(test_path, ranked_paths[:4])
        self.assertTrue(self._citations_for_path(context_pack, source_path))
        self.assertTrue(self._citations_for_path(context_pack, test_path))
        self.assertTrue(all(citation.get("snippet_allowed") is False for citation in context_pack["source_citations"]))

    def test_ab_behavior_constraint_notes_early_return_allowlist(self) -> None:
        repo = self.root / "langgraph-like"
        repo.mkdir()
        (repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        serde_dir = repo / "libs" / "checkpoint" / "langgraph" / "checkpoint" / "serde"
        tests_dir = repo / "libs" / "checkpoint" / "tests"
        serde_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        (serde_dir / "jsonplus.py").write_text(
            "def with_msgpack_allowlist(allowlist):\n"
            "    if allowlist is True:\n"
            "        return allowlist\n"
            "    allowed = set(allowlist or [])\n"
            "    allowed.add('builtins')\n"
            "    return sorted(allowed)\n\n"
            "def dumps_typed(value):\n"
            "    return ('json', value)\n",
            encoding="utf-8",
        )
        (tests_dir / "test_jsonplus.py").write_text(
            "from langgraph.checkpoint.serde.jsonplus import with_msgpack_allowlist\n\n"
            "def test_true_allowlist_uses_early_return():\n"
            "    assert with_msgpack_allowlist(True) is True\n\n"
            "def test_iterable_allowlist_adds_default():\n"
            "    assert 'builtins' in with_msgpack_allowlist(['custom'])\n",
            encoding="utf-8",
        )
        (serde_dir / "base.py").write_text(
            "def serialize(value):\n"
            "    return value\n",
            encoding="utf-8",
        )
        (serde_dir / "pickle.py").write_text(
            "def with_pickle_allowlist(allowlist):\n"
            "    return allowlist or []\n",
            encoding="utf-8",
        )
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        pack = RetrievalService(self.store).retrieve(
            "Fix with_msgpack_allowlist allowlist behavior and update tests",
            repo=result.repository.id,
            language="Python",
            limit=8,
        )
        trace = self.store.get_retrieval_trace(pack["trace_id"])
        context_pack = pack["context_pack"]
        ranked_paths = self._ranked_paths(trace)

        self.assertIn("libs/checkpoint/langgraph/checkpoint/serde/jsonplus.py", ranked_paths[:2])
        self.assertIn("libs/checkpoint/tests/test_jsonplus.py", ranked_paths[:5])
        context_text = " ".join(
            [
                pack["markdown"],
                " ".join(context_pack["risks"]),
                " ".join(context_pack["implementation_steps"]),
            ]
        ).lower()
        self.assertIn("allowlist", context_text)
        self.assertIn("early return", context_text)
        self.assertNotIn("expect true allowlists to add defaults", context_text)

    def test_ab_low_quality_warning_names_missing_exact_entity_and_suppresses_roles(self) -> None:
        repo = self.root / "missing-entity-like"
        repo.mkdir()
        (repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        config_dir = repo / "src" / "config"
        config_dir.mkdir(parents=True)
        (config_dir / "provider-config.ts").write_text(
            "export function loadProviderConfig(config: Record<string, string>) {\n"
            "  return config.provider ?? config.storage ?? config.apiKey;\n"
            "}\n",
            encoding="utf-8",
        )
        (config_dir / "storage-provider.ts").write_text(
            "export function loadStorageProvider(config: Record<string, string>) {\n"
            "  return config.storage ?? 'local';\n"
            "}\n",
            encoding="utf-8",
        )
        result = IngestionService(self.settings, self.store).ingest_local(repo)

        pack = RetrievalService(self.store).retrieve(
            "Fix MissingProviderResolver so provider config validation rejects unknown values",
            repo=result.repository.id,
            language="TypeScript",
            limit=5,
        )
        context_pack = pack["context_pack"]
        warning_text = " ".join(context_pack["risks"]).lower()

        self.assertIn("missingproviderresolver", warning_text)
        self.assertIn("inspect exact", warning_text)
        for noisy_path in ("src/config/provider-config.ts", "src/config/storage-provider.ts"):
            self.assertNotEqual("edit target", self._role_for_path(context_pack, noisy_path))

    def _write_repo(self, name: str, source: str) -> Path:
        repo = self.root / name
        repo.mkdir()
        (repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        package_dir = repo / "packages" / "graphrag" / "query"
        package_dir.mkdir(parents=True)
        (package_dir / "context_builder.py").write_text(source, encoding="utf-8")
        return repo

    def _ranked_paths(self, trace: dict) -> list[str]:
        return [
            str(item.get("path"))
            for item in trace["payload"]["ranking_details"]
            if item.get("path")
        ]

    def _role_for_path(self, pack: dict, path: str) -> str | None:
        for section in (
            pack["recommended_patterns"],
            pack["relevant_examples"],
            pack["architecture_rules"],
        ):
            for item in section:
                if any(citation.get("path") == path for citation in item["citations"]):
                    return item.get("role")
        return None

    def _citations_for_path(self, pack: dict, path: str) -> list[dict]:
        return [
            citation
            for citation in pack["source_citations"]
            if citation.get("path") == path
        ]
