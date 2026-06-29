from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalBenchmarkCase:
    id: str
    scenario: str
    query: str
    expected_roles: dict[str, str]
    pass_criteria: tuple[str, ...]
    test_name: str


RETRIEVAL_QUALITY_CASES: tuple[RetrievalBenchmarkCase, ...] = (
    RetrievalBenchmarkCase(
        id="graphrag_config_validation",
        scenario="GraphRAG-style config validation",
        query=(
            "Validate ChunkingConfig so token chunking rejects non-positive size, "
            "negative overlap, and overlap >= size; add unit tests."
        ),
        expected_roles={
            "primary_edit_target": "packages/graphrag-chunking/graphrag_chunking/chunking_config.py",
            "runtime_risk": "packages/graphrag-chunking/graphrag_chunking/token_chunker.py",
            "related_test": "tests/unit/chunking/test_chunker.py",
            "convention_example": "tests/unit/config/test_rate_limit_config.py",
        },
        pass_criteria=(
            "primary edit target appears in top 2",
            "runtime-risk file appears in top 4",
            "related test appears in top 5",
            "context mentions validation boundary and runtime risk",
        ),
        test_name="test_code_modification_task_promotes_exact_source_and_related_tests",
    ),
    RetrievalBenchmarkCase(
        id="fastapi_config_endpoint_validation",
        scenario="FastAPI config endpoint validation",
        query=(
            "Add validation to MCP server configuration so creating or updating a server "
            "rejects blank names and malformed URLs; update the FastAPI config endpoint tests."
        ),
        expected_roles={
            "primary_edit_target": "server/api/config/mcp.py",
            "runtime_persistence_boundary": "server/database/config/mcp_manager.py",
            "related_test": "server/tests/test_config.py",
            "convention_example": "server/api/config/validation.py",
            "runtime_consequence": "server/utils/mcp/client.py",
        },
        pass_criteria=(
            "API edit target appears in top 3",
            "endpoint test appears in top 5",
            "runtime/persistence boundary appears in top 5",
            "runtime consequence does not outrank edit target",
            "context labels edit target, runtime risk, related test, and convention",
        ),
        test_name="test_fastapi_config_validation_task_promotes_api_target_tests_and_risk",
    ),
    RetrievalBenchmarkCase(
        id="dotenv_parser_same_stem",
        scenario="Parser behavior and same-stem tests",
        query=(
            "Add support for escaping literal # characters in unquoted .env values "
            "while keeping whitespace-prefixed # comments working; update parser tests."
        ),
        expected_roles={
            "primary_edit_target": "src/dotenv/parser.py",
            "related_test": "tests/test_parser.py",
            "runtime_use_site": "src/dotenv/main.py",
            "convention_example": "tests/test_parser.py",
            "risk_context": "literal #, escaped hash, whitespace comments",
        },
        pass_criteria=(
            "parser edit target appears in top 2",
            "same-stem parser test appears in top 3",
            "runtime/use-site file appears in top 5",
            "citations are present",
            "context mentions concrete parser edge cases",
            "unrelated tests do not outrank the same-stem parser test",
        ),
        test_name="test_parser_task_pairs_same_stem_test_and_reports_edge_cases",
    ),
)


def retrieval_case(case_id: str) -> RetrievalBenchmarkCase:
    for case in RETRIEVAL_QUALITY_CASES:
        if case.id == case_id:
            return case
    raise KeyError(case_id)
