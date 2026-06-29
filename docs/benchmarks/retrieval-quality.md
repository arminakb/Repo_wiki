# Retrieval Quality Benchmark

## Purpose

This benchmark tracks whether repo-wiki retrieval gives coding agents the files and context they need before editing. It is a regression suite, not a marketing scorecard: results should come from runnable tests or a regenerated local report.

## What is measured

The benchmark checks:

- the query used for retrieval.
- expected files and their roles.
- actual rank constraints for edit targets, tests, runtime/use-site files, and conventions.
- source citation presence.
- context quality signals such as role labels, runtime risk notes, and concrete edge-case risks.
- retrieval latency recorded in the trace.
- noise control, especially unrelated tests outranking direct local tests.

## Benchmark cases

### Case A: GraphRAG-style config validation

Scenario: a task asks to validate a config model so invalid values are rejected and tests are updated.

Query:

```text
Validate ChunkingConfig so token chunking rejects non-positive size, negative overlap, and overlap >= size; add unit tests.
```

Expected roles/files:

| Role | Expected file |
| --- | --- |
| Primary edit target | `packages/graphrag-chunking/graphrag_chunking/chunking_config.py` |
| Runtime-risk file | `packages/graphrag-chunking/graphrag_chunking/token_chunker.py` |
| Related test file | `tests/unit/chunking/test_chunker.py` |
| Convention example | `tests/unit/config/test_rate_limit_config.py` |

Pass criteria:

- edit target appears in top 2.
- runtime-risk file appears in top 4.
- related test appears in top 5.
- noisy tests and unrelated generated/package files do not dominate.
- context mentions validation boundary and runtime risk.
- source citations are present.
- trace records retrieval latency.

Current result summary: covered by `test_code_modification_task_promotes_exact_source_and_related_tests`; passing in the fixture-backed unit suite.

Notes: this is a compact GraphRAG-like fixture, not a full live GraphRAG repository benchmark.

### Case B: FastAPI config endpoint validation

Scenario: a task asks to add validation to create/update API config endpoints and update endpoint tests.

Query:

```text
Add validation to MCP server configuration so creating or updating a server rejects blank names and malformed URLs; update the FastAPI config endpoint tests.
```

Expected roles/files:

| Role | Expected file |
| --- | --- |
| Primary edit target | `server/api/config/mcp.py` |
| Runtime/persistence boundary | `server/database/config/mcp_manager.py` |
| Related endpoint test | `server/tests/test_config.py` |
| Convention example | `server/api/config/validation.py` |
| Runtime consequence file | `server/utils/mcp/client.py` |

Pass criteria:

- API edit target appears in top 3.
- endpoint test appears in top 5.
- runtime/persistence boundary appears in top 5.
- runtime consequence file can appear but must not outrank the edit target.
- context labels edit target, runtime risk, related test, and validation convention.
- unrelated chat/database tests do not outrank the direct endpoint test.
- source citations are present.
- trace records retrieval latency.

Current result summary: covered by `test_fastapi_config_validation_task_promotes_api_target_tests_and_risk`; passing in the fixture-backed unit suite.

Notes: this case models the Phlox retrieval shape with a small FastAPI fixture so normal unit tests do not need to clone or index the full repository.

### Case C: Parser behavior and same-stem tests

Scenario: a task asks to support escaping literal `#` characters in unquoted `.env` values while preserving whitespace-prefixed comments.

Query:

```text
Add support for escaping literal # characters in unquoted .env values while keeping whitespace-prefixed # comments working; update parser tests.
```

Expected roles/files:

| Role | Expected file |
| --- | --- |
| Primary edit target | `src/dotenv/parser.py` |
| Related same-stem test | `tests/test_parser.py` |
| Runtime/use-site file | `src/dotenv/main.py` |
| Convention/example | `tests/test_parser.py` parametrized parser cases |
| Risk-revealing context | literal `#`, escaped hash, whitespace comments |

Pass criteria:

- parser edit target appears in top 2.
- same-stem parser test appears in top 3.
- runtime/use-site file appears in top 5.
- citations are present.
- context mentions concrete parser edge cases.
- unrelated tests do not outrank the same-stem parser test.
- trace records retrieval latency.

Current result summary: covered by `test_parser_task_pairs_same_stem_test_and_reports_edge_cases`; passing in the fixture-backed unit suite. A manual python-dotenv rerun also produced `parser.py` rank 1, `test_parser.py` rank 2, and `main.py` rank 4.

Notes: the unit test uses a python-dotenv-like fixture. Real-repo reruns should be recorded separately when performed.

## Pass criteria

The benchmark passes when all three case tests pass and the context pack includes the expected role signals, citations, and risk/context notes. Rank checks are intentionally role-specific rather than a single aggregate score.

## How to run

Run the fixture-backed benchmark cases:

```bash
python3 -m unittest tests.test_retrieval_quality -v
```

Run the broader local regression suite:

```bash
python3 -m unittest tests.test_end_to_end -v
python3 -m compileall repo_wiki
```

Generate the local smoke benchmark report for whatever is currently indexed:

```bash
python3 -m repo_wiki.interfaces.cli benchmark report --output docs/benchmarks/mvp-results.md
```

## Latest results

Latest verified local run:

| Suite | Result |
| --- | --- |
| `tests.test_retrieval_quality` | 14 tests passed |
| `tests.test_end_to_end` | 20 tests passed |
| `python3 -m compileall repo_wiki` | passed |

The case tests are fixture-level measurements. Latency is recorded in each retrieval trace, but the unit suite does not enforce a fixed latency threshold.

## Known limitations

- The formal regression cases use synthetic fixtures that preserve the retrieval shape of the real scenarios.
- Latency numbers are fixture-level and machine-dependent.
- The real python-dotenv, GraphRAG, and Phlox repositories are not cloned during normal unit tests.
- The benchmark is an early engineering regression suite, not an academic IR evaluation.
- The MVP report in `mvp-results.md` measures the currently indexed local database and may not include these three judged cases unless run in a prepared environment.

## Next benchmark improvements

- Add an optional real-repo benchmark runner for locally available GraphRAG, Phlox, and python-dotenv checkouts.
- Persist per-case rank, citation, and latency results to a generated report.
- Add more languages and frameworks beyond Python/FastAPI/parser cases.
- Track noisy-result categories explicitly.
- Run real agent A/B evaluations with and without repo-wiki context.
