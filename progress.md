# Progress

Overall progress: [██████████] 100%

Local MVP hardening, publication prep, and final release gate are complete for a GitHub-ready local MVP.

## Tracker

| Phase | Status | Report |
| --- | --- | --- |
| 0. Full Project Review and Baseline | Done | Baseline recorded below. |
| 1. Issue Resolution - Runtime, Test, and Data Hygiene | Done | Runtime/data hygiene fixes recorded below. |
| 2. Issue Resolution - SAS Core Contract Gaps | Done | Core contract fixes recorded below. |
| 3. Issue Resolution - Interface Contract Completion | Done | Interface contract fixes recorded below. |
| 4. Optimization - Retrieval Quality and Pipeline Performance | Done | Retrieval quality and benchmark fixes recorded below. |
| 5. Optimization - Code Structure, Maintainability, and Storage | Done | Storage/config fixes recorded below. |
| 6. Production Readiness - Reliability, Security, and Error Handling | Done | Reliability/security fixes recorded below. |
| 7. Production Readiness - Test Matrix, CI, and Real Environment Validation | Done | Test matrix, CI, and validation fixes recorded below. |
| 8. Publication - GitHub Repository Preparation | Done | Release prep recorded below. |
| 9. Final Production Gate | Done | Final gate recorded below. |

## Current Status

This branch completes the local MVP release gate. The project is ready for GitHub publication as a local-first repository knowledge compiler, with benchmark-scope limitations stated plainly.

Latest verification on 2026-06-22:

- `python3 -m compileall repo_wiki` passed.
- `RUFF_CACHE_DIR=/tmp/repo-wiki-phase89-ruff-cache /tmp/repo-wiki-phase89-venv/bin/python -m ruff check .` passed.
- `git diff --check` passed.
- Local release index passed: 80 files, 297 symbols, 35 knowledge objects, 425 graph nodes, 791 graph edges.
- Benchmark report regeneration passed: 5 tasks, average latency 14 ms, citation coverage 1.0, per-category quality recorded in `docs/benchmarks/mvp-results.md`.
- MCP-compatible stdio `tools/list` and `retrieve_context` passed against the release index.
- HTTP contract smoke passed through `tests.test_end_to_end.EndToEndTest.test_phase3_interface_contracts_are_consistent`.
- Bundled GraphRAG slice ingest passed: 155 files, 455 symbols, 49 knowledge objects, 661 graph nodes, 1,102 graph edges, 1,032 ms.
- Bundled GraphRAG retrieval for `how does GraphRAG build query context` returned `packages/graphrag/graphrag/query/context_builder/community_context.py` and `packages/graphrag/graphrag/index/operations/summarize_communities/graph_context/context_builder.py`.

What changed in this pass:

- Retrieval now accepts an actual `repo` filter through core, CLI, HTTP, and MCP-compatible stdio paths.
- SQLite FTS, vector, and graph-expanded retrieval candidates are filtered by source refs from the requested repository.
- `tests/test_retrieval_quality.py` now covers repo-scoped retrieval and the GraphRAG query-context expected path.
- Context packs now carry the stable `context_pack.v1` schema marker.
- Benchmark reports include expected-file hits, top-k precision, and per-category quality when judged tasks provide expected paths.
- ADR Markdown files now compile into cited `DecisionRecord` knowledge objects.
- Repeated source folders with at least two files now compile into cited `ModulePattern` objects.
- Code-path query terms now split `/`, `.`, and `_` pieces so query/context-builder paths rank correctly.
- Docs now separate measured MVP status from planned portfolio targets, document the bundled GraphRAG dataset policy, include MCP setup/transcript examples, and add v0.1.0 release notes.

## Post-Release Follow-Ups

Do not claim portfolio-scale completion until these are real:

1. Expand benchmarks to the planned 10 small plus 10 medium repos, with at least 50 judged tasks across backend, frontend, testing, refactor, and bug-fix categories.
2. Validate against a real external MCP client after choosing the target client; the repo now documents the exact command config and a successful local transcript shape.
3. Add semantic retrieval or TypeScript compiler-backed extraction only if judged benchmark failures prove the current local/scanner approach is the bottleneck.
4. Keep release claims limited to measured local MVP behavior until larger benchmark runs exist.

## Phase Reports

### Phase 0: Full Project Review and Baseline

Status: Done.

Scope reviewed:

- Source of truth and operating docs: `SAS.md`, `AGENT.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `README.md`, `ROADMAP.md`.
- ADRs: `docs/adr/0001-local-first-storage.md` through `docs/adr/0004-documentation-first-class.md`.
- Architecture, API, usage, example, benchmark, development, and diagram docs under `docs/`.
- Main packages under `repo_wiki/`: domain, config, ingestion, extraction, compilation, storage, graph, retrieval, reflexion, CLI, HTTP, MCP, benchmark, discovery, bootstrap, live fallback, inspector.
- Tests: `tests/test_end_to_end.py`.

Baseline inventory against SAS requirements:

- Ingestion `FR-ING-*`: local path ingestion works; GitHub URL ingestion exists through shallow `git clone`; repo metadata, include/exclude patterns, generated/dependency directory skipping, file hashes, snapshot hashes, license metadata, and snippet flags exist. Gaps: Git repository discovery fails at workspace root, GitHub publication state is unresolved, GitHub stars/default branch are not populated by clone ingestion, restartability/error logging is minimal, failed-file metrics are sparse.
- Extraction `FR-EXT-*`: file tree, Python AST symbols/imports/docstrings, TypeScript/JavaScript regex symbols/imports/exports/components/routes, package manifests, Markdown headings/fences/links, route detection, test-path detection, test edges, and extraction event counts exist. Gaps: Python call references are not really extracted as graph calls, TypeScript parser is regex-based, test-to-source linking is heuristic-only, Markdown hierarchy is shallow, extraction failure events are not persisted per file.
- Knowledge compilation `FR-KC-*`: ProjectProfile, ArchitecturePattern, ImplementationPattern, TestingPattern, and AntiPattern generation exist with Pydantic validation, source refs, scoring, and dedupe. Gaps: several SAS object types are enum-only or deferred (`ModulePattern`, `SecurityPattern`, `DecisionRecord`, `CodeExample`, `Constraint`, `Tradeoff`), source refs are broad whole-file ranges, snippets are not returned but citation/snippet policy is not strongly enforced in retrieval.
- Retrieval `FR-RET-*`: natural-language retrieval, filters, task classification, SQLite FTS5, deterministic local vector scoring, graph expansion, rerank, JSON/Markdown context packs, citations, and traces exist. Gaps: quality on real repo query is weak, token budget is word-count based, license policy is recorded but not actively filtering returned citations, trace ranking details are limited, context packs can cite unrelated project-profile files.
- Interfaces `FR-IF-*`: CLI, stdlib HTTP server, optional FastAPI app factory, and JSON-RPC MCP-like stdio adapter call core services. Gaps: CLI uses `argparse` not Typer, FastAPI payloads are raw dicts not Pydantic request models, MCP adapter is not official SDK-based, interface contract tests are thin.
- Reflexion `FR-REF-*`: feedback, objective signals, staged knowledge, scoring, promotion/rejection, provenance edge, and CLI/MCP/API paths exist. Gaps: dedupe/promotion policy is simple, staged validation is light, promotion can create sparse knowledge when context lacks citations.
- Non-functional: local-first SQLite, FTS, hash vectors, docs, diagrams, ADRs, CI, tests, and `.gitignore` exist. Gaps: schema lives inline with lightweight migration functions instead of explicit migration files, config is env-only rather than `repo-wiki.toml`, structured logging is absent, domain error hierarchy is incomplete, security/license tests need expansion, benchmark results need clearer real-command provenance.

Commands run:

- `python3 -m compileall repo_wiki` passed.
- `python3 -m unittest discover -s tests -v` passed: 7 tests, 0 failures.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-cli python3 -m repo_wiki.interfaces.cli doctor` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-cli python3 -m repo_wiki.interfaces.cli status` passed.
- Small smoke: `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-small python3 -m repo_wiki.interfaces.cli ingest local tests` passed: 1 file, 2 knowledge objects, 5 graph edges.
- Small retrieval smoke passed for `add end to end tests for retrieval`; quality gate passed with score 0.6.
- GraphRAG targeted slice ingest passed: 155 files, 455 symbols, 21 knowledge objects, 805 graph edges.
- Full `dataset/graphrag-main/` ingest passed: 725 files, 2,120 symbols, 71 dependencies, 24 knowledge objects, 2,942 graph nodes, 7,215 graph edges, duration 1,380 ms.
- GraphRAG retrieval smoke passed mechanically for `how does GraphRAG build query context`, but returned weakly relevant vector-store/context-adjacent results.
- Benchmark report to `/tmp/repo-wiki-roadmap-graphrag-full/mvp-results.md` passed: 3 tasks, average returned items 5, average citation count 9.67.
- MCP stdio smoke passed for `tools/list` and `retrieve_context`.
- HTTP loopback smoke passed after escalation because sandbox blocked socket bind: `/health` and `/v1/metrics` returned JSON.

Generated artifact hygiene:

- `.gitignore` covers `.repo-wiki/`, `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, virtualenvs, build outputs, and `.env`.
- `compileall` and tests generated `__pycache__/` and `.pyc` files under `repo_wiki/` and `tests/`; these are ignored but present after Phase 0.
- Runtime databases and benchmark outputs were written under `/tmp/repo-wiki-roadmap-*`, not source.
- Real tests under `tests/` are preserved.
- No root `.repo-wiki/` database was created during Phase 0.
- The workspace has a `.git` entry, but `git status --short --branch` fails with `fatal: not a git repository`; publication hygiene and commit history remain unresolved.

Concrete weak behavior and risks:

- Retrieval relevance needs work: the GraphRAG context query ranked vector-store files and broad project-profile citations ahead of more query-specific files/docs.
- Query classification labeled `how does GraphRAG build query context` as `frontend_feature`.
- Project type and framework detection for GraphRAG stayed `unknown` despite Python packages and pyproject files.
- Source citations often cover entire files, including long files over 300 lines.
- HTTP smoke requires socket permissions in this sandbox.
- Official FastAPI/Typer/MCP SDK recommendations are implemented as lightweight alternatives or deferred in docs.
- No production code changes were made before this Phase 0 report.

### Phase 1: Issue Resolution - Runtime, Test, and Data Hygiene

Status: Done.

What changed:

- Added `.gitignore` coverage for local SQLite files, SQLite sidecars, benchmark scratch reports, `reports/`, and `tmp/`.
- Fixed local ingestion so a custom `Settings.data_dir` inside the indexed repository is skipped even when it is not named `.repo-wiki`.
- Reused the same generated-data skip in snapshot hashing so generated DB/vault files do not perturb snapshot IDs.
- Added a regression test: `test_ingest_skips_custom_data_dir_inside_repo`.
- Removed generated `__pycache__/` directories after verification.

Commands run:

- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_ingest_skips_custom_data_dir_inside_repo -v` failed before the fix and passed after it.
- `python3 -m compileall repo_wiki` passed.
- `python3 -m unittest discover -s tests -v` passed: 8 tests, 0 failures.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase1 python3 -m repo_wiki.interfaces.cli doctor` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase1 python3 -m repo_wiki.interfaces.cli status` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase1-ingest python3 -m repo_wiki.interfaces.cli ingest local tests` passed.
- MCP `tools/list` smoke passed against the temp data dir.

Results and remaining risks:

- Compile, unit tests, CLI smoke, local ingest smoke, and MCP smoke are green.
- HTTP smoke was already verified in Phase 0; it requires loopback socket permission in this sandbox.
- Root-generated `.repo-wiki/` was not created during Phase 1; temp databases stayed under `/tmp`.
- Generated Python caches are ignored and were cleaned after checks.
- Git remains unusable at workspace root, so tracked/untracked publication hygiene cannot be verified through `git status`.
- README command examples were inspected during Phase 0, but external GitHub commands and long-running service commands were not all executed in Phase 1 because network/server work belongs to later interface/publication phases.
- Indexed repository code is read as text only; no imports/execution of indexed code were added.

### Phase 2: Issue Resolution - SAS Core Contract Gaps

Status: Done.

What changed:

- Added deterministic Python call extraction for direct `name()` and attribute `.name()` calls inside Python functions/methods.
- Added `CALLS` graph edges between symbols in the same file when both caller and callee are indexed symbols.
- Wired call extraction through `ExtractionService` into `GraphBuilder`.
- Added a regression assertion to the end-to-end ingestion flow to require a `CALLS` edge.
- Added line-specific source references derived from indexed symbol spans so implementation and testing patterns can cite useful line ranges instead of only whole files.
- Enforced retrieval citation policy: `metadata_only`, `private_local_only`, and `permissive_only` return only citations whose stored source refs allow snippets; `allow_all_public` remains the explicit bypass.
- Added regression coverage for `metadata_only` retrieval so source citations and per-item citations are omitted while derived summaries remain available.
- Expanded the fixture and contract test coverage for TypeScript/Next.js route extraction, package manifest parsing, Markdown headings/fences/links, and test-to-source graph links.
- Replaced the TypeScript/JavaScript regex declaration/import extractor with a small stdlib token scanner that ignores comments and strings, preserves import/export module specifiers, and returns multi-line declaration spans.
- Accepted Markdown fenced code blocks with optional whitespace after the opening backticks.
- Clarified retrieval ranking text from "source citations" to "source references" because citations can be filtered by policy.
- Added `.worktrees/` to `.gitignore` so the per-phase worktree directories remain untracked.

Commands run:

- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_ingest_retrieve_feedback_and_mcp -v` failed before the fix because `CALLS` was absent, then passed after the fix.
- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_implementation_citations_use_symbol_line_ranges tests.test_end_to_end.EndToEndTest.test_metadata_only_retrieval_omits_source_citations -v` failed before the fixes and passed after them.
- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_core_extractors_cover_typescript_routes_docs_packages_and_tests -v` exposed the Markdown fence assertion issue and passed after the test/regex adjustment.
- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_typescript_extractor_ignores_comments_strings_and_spans_blocks -v` failed against the regex extractor because it indexed an import inside a template string, then passed after the scanner replacement.
- `python3 -m compileall repo_wiki` passed.
- `python3 -m unittest discover -s tests -v` passed: 12 tests, 0 failures.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase2-graphrag python3 -m repo_wiki.interfaces.cli ingest local dataset/graphrag-main --include 'packages/graphrag/graphrag/index/**' --include 'packages/graphrag/graphrag/query/**' --include 'tests/unit/query/**' --include 'README.md' --include 'pyproject.toml'` passed: 155 files, 455 symbols, 1,033 graph edges.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase2-final python3 -m repo_wiki.interfaces.cli doctor` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase2-final python3 -m repo_wiki.interfaces.cli status` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase2-graphrag-final python3 -m repo_wiki.interfaces.cli ingest local dataset/graphrag-main --include 'packages/graphrag/graphrag/index/**' --include 'packages/graphrag/graphrag/query/**' --include 'tests/unit/query/**' --include 'README.md' --include 'pyproject.toml' --license-policy metadata_only` passed: 155 files, 455 symbols, 21 knowledge objects, 633 graph nodes, 1,033 graph edges, 271 source refs.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase2-graphrag-final python3 -m repo_wiki.interfaces.cli retrieve 'how does GraphRAG build query context' --license-policy metadata_only --format json` passed mechanically and returned an empty `source_citations` list under metadata-only policy.

Results and remaining risks:

- Core SAS Version 1 gates now have deterministic coverage for local ingestion, include/exclude handling, Python call references, TypeScript/JavaScript symbols/routes, package manifests, Markdown docs, test links, cited knowledge objects, deduped objects, source refs, retrieval citation policy, and real-repo slice ingestion.
- GitHub URL ingestion remains implemented as shallow clone but was not network-tested in Phase 2 because network publication validation belongs to later phases.
- Call extraction remains intentionally basic and intra-file only; cross-module call resolution is deferred until measured retrieval needs it.
- TypeScript extraction is no longer regex-based, but remains a lightweight stdlib scanner rather than a full TypeScript compiler AST; no TypeScript call graph is generated yet.
- Additional enum values such as `ModulePattern`, `SecurityPattern`, `CodeExample`, `Constraint`, and `Tradeoff` remain deferred until the compiler has deterministic evidence for them; SAS Version 1 required generated types are covered.
- Retrieval relevance on GraphRAG still needs Phase 4 quality work; this phase only hardened citations and core extraction contracts.
- Generated runtime databases stayed under `/tmp`; source caches are ignored.

### Phase 3: Issue Resolution - Interface Contract Completion

Status: Done.

What changed:

- Added CLI coverage for SAS command aliases that were missing from the parser: `ingest status`, `extract`, and `compile --no-llm`.
- Kept the CLI on `argparse` for Version 1 and documented the dependency-light interface decision in `docs/adr/0005-thin-stdlib-interfaces-for-version-1.md`.
- Added Pydantic HTTP request models for repository ingest, local ingest, retrieval, feedback, and staged-feedback decisions.
- Wired those HTTP models through both the optional FastAPI app factory and the standard-library HTTP handler.
- Kept the stdlib HTTP server as the runnable fallback and documented the optional FastAPI path.
- Added MCP `repo` argument support for `retrieve_context`, returned top-level `citations`, added `list_feedback`, and exposed `repo-wiki://feedback`.
- Kept the MCP adapter as a thin JSON-RPC stdio adapter and documented deferral of the official MCP SDK until it improves behavior instead of just adding dependency weight.
- Updated CLI, HTTP, and MCP docs/examples for the Phase 3 public contract.
- Added a Phase 3 interface contract regression test covering CLI aliases, HTTP model validation, direct stdlib HTTP handler behavior, MCP retrieve shape, MCP feedback listing, and MCP resources.

Commands run:

- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_phase3_interface_contracts_are_consistent -v` failed before the CLI/MCP/HTTP fixes and passed after them.
- `python3 -m compileall repo_wiki` passed.
- `python3 -m unittest discover -s tests -v` passed: 13 tests, 0 failures.
- `git diff --check` passed.

Results and remaining risks:

- CLI, HTTP, and MCP now expose the same core retrieval behavior and consistent context pack shapes.
- Public interface examples are updated for the current dependency-light implementation.
- FastAPI remains optional; the stdlib HTTP handler is covered without binding a socket.
- Typer and official MCP SDK remain deferred by ADR because they add dependencies without changing the Version 1 contract surface.
- HTTP error mapping is still basic and belongs to Phase 6 reliability/error-hardening work.
- GitHub network ingestion and long-running server validation remain later real-environment/publication tasks.

### Phase 4: Optimization - Retrieval Quality and Pipeline Performance

Status: Done.

What changed:

- Added query-overlap scoring to retrieval so query-specific files and symbols can outrank broad context-adjacent results.
- Fixed SQLite FTS BM25 normalization so stronger matches receive stronger lexical scores.
- Added token-aware task/domain matching to avoid substring false positives like `query` matching `ui`; restored plural `tests`/`specs` handling for test-generation queries.
- Added retrieval trace payloads with candidate counts and ranking details, including lexical, vector, graph, and query-overlap signals.
- Added `SQLiteStore.get_retrieval_trace()` for trace inspection in tests and benchmark reporting.
- Expanded the benchmark report from a 3-task smoke report to a 5-task retrieval quality suite covering backend, frontend, testing, refactor, and bug-fix tasks.
- Added benchmark latency, citation coverage, and per-task candidate-count reporting.
- Fixed compiler domain inference to use path tokens instead of substring matches.
- Added Phase 4 regression coverage for GraphRAG query-context retrieval, trace details, report metrics, and token-budget behavior.

Commands run:

- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_ingest_retrieve_feedback_and_mcp -v` failed before the benchmark-report update because the report lacked the Phase 4 quality fields, then passed after the fix.
- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_phase4_retrieval_prioritizes_query_context_and_records_ranking_details -v` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase4-graphrag python3 -m repo_wiki.interfaces.cli ingest local dataset/graphrag-main --include 'packages/graphrag/graphrag/index/**' --include 'packages/graphrag/graphrag/query/**' --include 'tests/unit/query/**' --include 'README.md' --include 'pyproject.toml'` passed: 155 files, 455 symbols, 21 knowledge objects, 633 graph nodes, 1,074 graph edges, duration 1,387 ms.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase4-graphrag python3 -m repo_wiki.interfaces.cli retrieve 'how does GraphRAG build query context' --format json` passed and ranked context-builder files first, including `packages/graphrag/graphrag/index/operations/summarize_communities/graph_context/context_builder.py`, `packages/graphrag/graphrag/query/context_builder/builders.py`, and `packages/graphrag/graphrag/query/context_builder/community_context.py`.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase4-graphrag python3 -m repo_wiki.interfaces.cli benchmark report --output /tmp/repo-wiki-roadmap-phase4-graphrag/mvp-results.md` passed: 5 tasks, average returned items 5, average citation count 9, average latency 22.8 ms, citation coverage 1.0.
- `python3 -m compileall repo_wiki` passed.
- `python3 -m unittest discover -s tests -v` passed: 14 tests, 0 failures.
- `git diff --check` passed.

Results and remaining risks:

- Retrieval now returns useful cited context packs for the representative Python/GraphRAG query and the fixed benchmark suite.
- The measured GraphRAG slice retrieval latency is well under the 5 second MVP target; local test indexes are under the 2 second small-index target.
- Context packs retain recommendations, examples, tests to consider, risks, citations, and trace IDs.
- The quality suite is reproducible through the existing benchmark report path and uses temp data outside tracked source during validation.
- The SAS portfolio-scale 50-task judged evaluation remains future work; Phase 4 adds an MVP fixed suite and mechanical citation/latency evidence.
- TypeScript retrieval quality is represented through fixture and benchmark task coverage, but a real large TypeScript repository benchmark still belongs to Phase 7 real-environment validation.
- Token budgeting still uses approximate word counts; it is bounded and tested, but exact model-token accounting remains deferred.

### Phase 5: Optimization - Code Structure, Maintainability, and Storage

Status: Done.

What changed:

- Created the Phase 5 worktree at `.worktrees/roadmap-phase-5-storage-config` from `roadmap-phase-4-retrieval-quality`.
- Audited module boundaries against the SAS layering rule. Interfaces call core services, storage owns SQL, extractors own parsing, retrieval owns ranking/context, graph owns graph operations, and reflexion remains under `repo_wiki/core/reflexion_service.py`. No circular dependency or duplicate logic justified a split.
- Kept `repo_wiki/storage/sqlite.py` intact instead of splitting it; the module is large, but moving code now would be mechanical churn without a clearer production boundary.
- Added `repo-wiki.toml` support through `Settings.from_env()` using stdlib `tomllib`.
- Added typed settings for storage paths, max file size, default excludes, license policy, default retrieval tokens, and disabled LLM provider.
- Kept environment variables as overrides for config-file values.
- Wired configured default excludes into file discovery and snapshot hashing.
- Wired configured default retrieval token budget into CLI query/retrieve defaults.
- Exposed `SQLiteStore.schema_version()` over the existing `schema_migrations` table.
- Documented the storage/config decision in `docs/adr/0006-versioned-sqlite-and-toml-config.md` and added it to `DECISIONS.md`.
- Documented the optional `repo-wiki.toml` shape in `docs/development/setup.md`.
- Added regression tests for TOML config/env overrides and schema migration version recording.
- Added a legacy-schema upgrade regression test proving migrations add missing columns without losing existing feedback/staging rows.

Commands run:

- Phase 5 worktree baseline: `python3 -m compileall repo_wiki` passed.
- Phase 5 worktree baseline: `python3 -m unittest discover -s tests -v` passed: 14 tests, 0 failures.
- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_repo_wiki_toml_config_and_env_overrides tests.test_end_to_end.EndToEndTest.test_storage_schema_version_is_recorded -v` failed before production changes for the intended missing TOML/schema-version behavior, then passed after the fixes.
- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_storage_initialize_upgrades_legacy_schema_without_losing_rows -v` first failed because the regression test was absent, then passed after adding the legacy-upgrade coverage.
- `python3 -X tracemalloc=10 -W default::ResourceWarning -m unittest tests.test_end_to_end.EndToEndTest.test_storage_initialize_upgrades_legacy_schema_without_losing_rows tests.test_end_to_end.EndToEndTest.test_strategy_command_aliases_and_stack_detector -v` passed after closing the legacy setup SQLite connection explicitly.
- `python3 -m compileall repo_wiki` passed.
- `python3 -m unittest discover -s tests -v` passed: 17 tests, 0 failures.
- `git diff --check` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase5-final python3 -m repo_wiki.interfaces.cli doctor` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase5-final python3 -m repo_wiki.interfaces.cli status` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase5-final-ingest python3 -m repo_wiki.interfaces.cli ingest local tests` passed: 1 file, 2 knowledge objects, 5 graph edges.

Results and remaining risks:

- Core business logic remains independent from CLI/HTTP/MCP; no interface-to-core inversion was introduced.
- Database schema is explicitly versioned through the existing `schema_migrations` table and now has a public version accessor.
- Config is reproducible, documented, and test-covered without adding dependencies.
- SQLite writes already use connection context managers for transaction boundaries; deeper storage error taxonomy belongs to Phase 6.
- SQL indexes were inspected and left unchanged because Phase 4 retrieval latency was already under targets and no measured query justified another index.
- Generated runtime databases stayed under `/tmp`; source caches remain ignored.

### Phase 6: Production Readiness - Reliability, Security, and Error Handling

Status: Done.

What changed:

- Created the Phase 6 worktree at `.worktrees/roadmap-phase-6-reliability-security` from the committed Phase 5 branch.
- Completed the domain error hierarchy for expected repository, source, license, extraction, knowledge validation, retrieval, storage, and MCP validation failures.
- Mapped expected errors to readable CLI failures, typed HTTP JSON error envelopes, and JSON-RPC MCP errors.
- Added structured JSON log events for ingestion completion, retrieval traces, API requests, MCP tool calls, and feedback submission using the standard library logger.
- Hardened file discovery against path traversal through symlinks, null-byte binary files, oversized files, `.env` files, generated data dirs, and obvious secrets/private keys.
- Validated license policy names and preserved the existing snippet policy behavior: permissive-only citations require permissive licenses, metadata/private modes omit citations, and allow-all-public is explicit.
- Added SQLite `integrity_check`, `backup_to`, and `restore_from` helpers.
- Added CLI `backup create` and `backup restore`.
- Expanded `doctor` to report config load, schema version, SQLite integrity, git, storage writability, and optional FastAPI state.
- Documented backup commands in CLI and development setup docs.
- Added a Phase 6 regression test covering security filtering, redaction, license citation behavior, backup/restore integrity, HTTP/MCP error envelopes, structured logs, and doctor checks.

Commands run:

- Phase 6 worktree baseline: `python3 -m compileall repo_wiki` passed.
- Phase 6 worktree baseline: `python3 -m unittest discover -s tests -v` passed: 17 tests, 0 failures.
- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_phase6_reliability_security_and_backup_contracts -v` failed before the Phase 6 implementation, then passed after the fixes.
- `python3 -X tracemalloc=10 -W default::ResourceWarning -m unittest tests.test_end_to_end.EndToEndTest.test_phase6_reliability_security_and_backup_contracts -v` passed after explicitly closing the backup SQLite connection.
- `python3 -m compileall repo_wiki` passed.
- `python3 -m unittest discover -s tests -v` passed: 18 tests, 0 failures.
- `git diff --check` passed.

Results and remaining risks:

- Interfaces now handle expected failures without raw 500-style responses for common user errors.
- Security coverage includes symlink traversal prevention, binary skipping, max file size, `.env` exclusion, and secret/private-key redaction.
- License policy is enforced in retrieval citations without adding legal complexity or code snippet returns.
- Backup/restore is local SQLite-only and intentionally minimal; no cloud or scheduled backup service was added.
- Structured logs are JSON messages on the `repo_wiki` logger; production log routing/format configuration remains an operator concern.
- Deeper extraction failure persistence and richer storage error recovery remain possible future hardening, but the Phase 6 acceptance gate is covered.

### Phase 7: Production Readiness - Test Matrix, CI, and Real Environment Validation

Status: Done.

What changed:

- Created the Phase 7 worktree at `.worktrees/roadmap-phase-7-test-ci-validation` from the committed Phase 6 branch after pruning a stale missing worktree record.
- Updated CI to install the dev extra, run `compileall`, run `ruff check .`, and run the unit/integration test suite.
- Added Ruff configuration to exclude `dataset/graphrag-main/` so lint validates this project instead of the benchmark fixture.
- Removed one unused variable found by the new lint check.
- Updated README and testing docs with install, compile, lint, test, API, MCP, and benchmark commands.
- Regenerated `docs/benchmarks/mvp-results.md` from an actual local temp index and benchmark report command.
- Added a Phase 7 regression test covering CI, docs, benchmark report fields, and lint fixture exclusion.

Commands run:

- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_phase7_release_docs_and_ci_contract -v` failed before CI/docs/report updates, then passed after the fixes.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase7 python3 -m repo_wiki.interfaces.cli init` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase7 python3 -m repo_wiki.interfaces.cli ingest local . --include 'repo_wiki/**/*.py' --include 'tests/**/*.py' --include 'README.md' --include 'docs/**/*.md' --exclude 'dataset/**'` passed: 79 files, 294 symbols, 15 knowledge objects, 401 graph nodes, 757 graph edges.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase7 python3 -m repo_wiki.interfaces.cli retrieve 'add regression tests for HTTP errors' --format json` passed and returned a cited context pack.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase7 python3 -m repo_wiki.interfaces.cli feedback submit --context-pack ctx_be90bc005821447d --accepted --note 'phase7 validation smoke'` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase7 python3 -m repo_wiki.interfaces.cli graph export --format mermaid --output /tmp/repo-wiki-roadmap-phase7/knowledge.graph.mmd` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase7 python3 -m repo_wiki.interfaces.cli metrics` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase7 python3 -m repo_wiki.interfaces.cli benchmark report --output docs/benchmarks/mvp-results.md` passed and wrote real metrics: 5 benchmark tasks, average latency 5 ms, citation coverage 1.0.
- `python3 -m compileall repo_wiki` passed.
- `python3 -m unittest discover -s tests -v` passed: 19 tests, 0 failures.
- `RUFF_CACHE_DIR=/tmp/repo-wiki-phase7-ruff-cache /tmp/repo-wiki-phase7-venv/bin/python -m ruff check .` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase7-final python3 -m repo_wiki.interfaces.cli doctor` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase7-final python3 -m repo_wiki.interfaces.cli status` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-roadmap-phase7-final-ingest python3 -m repo_wiki.interfaces.cli ingest local tests` passed.
- MCP `tools/list` smoke passed through `repo_wiki.interfaces.cli mcp serve`.
- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_phase3_interface_contracts_are_consistent -v` passed as the HTTP/API contract smoke.
- `git diff --check` passed.

Results and remaining risks:

- CI now matches the documented local verification commands.
- The real local validation flow covers clean temp storage, local ingest, retrieval, feedback staging, graph export, metrics, MCP smoke, and benchmark report generation.
- The installed console script is configured in `pyproject.toml`; local validation used module commands because this environment's system Python is externally managed. A temporary venv under `/tmp` verified dev dependency installation and Ruff.
- `dataset/graphrag-main/` remains available for ingestion/benchmark stress validation but is excluded from repository lint.
- Generated runtime databases, graph export, Ruff cache, and venv stayed under `/tmp`; generated `__pycache__` directories were removed after verification.

### Phase 8: Publication - GitHub Repository Preparation

Status: Done.

What changed:

- Added `CHANGELOG.md` with v0.1.0 features, limitations, and follow-up scope.
- Added `docs/release/v0.1.0.md` with release notes and recommendation.
- Updated README to document `context_pack.v1` and per-category benchmark quality.
- Updated MCP setup docs with an exact client command config.
- Updated MCP examples with a successful `retrieve_context` transcript shape.
- Regenerated `docs/benchmarks/mvp-results.md` from a real temp release index.
- Added release-gate regression coverage for release docs, MCP docs, benchmark report shape, and final progress status.

Commands run:

- `python3 -m unittest tests.test_retrieval_quality.RetrievalQualityTest.test_repo_scoped_retrieval_returns_only_requested_repo_citations tests.test_retrieval_quality.RetrievalQualityTest.test_benchmark_report_groups_quality_by_task_category -v` failed before the context-pack schema and per-category benchmark changes, then passed after them.
- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_phase8_release_docs_and_final_gate_are_recorded -v` failed before release docs/progress updates, then passed after them.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-phase89 python3 -m repo_wiki.interfaces.cli ingest local . --include 'repo_wiki/**/*.py' --include 'tests/**/*.py' --include 'README.md' --include 'docs/**/*.md' --exclude 'dataset/**'` passed: 80 files, 297 symbols, 35 knowledge objects, 425 graph nodes, 791 graph edges.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-phase89 python3 -m repo_wiki.interfaces.cli benchmark report --output docs/benchmarks/mvp-results.md` passed: 5 tasks, average latency 14 ms, citation coverage 1.0.

Results and remaining risks:

- Release docs now summarize features, limits, and measured benchmark status without claiming unrun portfolio-scale numbers.
- `.gitignore` already excludes local databases, caches, temp reports, env files, and worktree directories.
- Git status works in this linked worktree; final state is not clean because intentional release files and code/test/docs changes are present.
- The 20-repository MVP benchmark target remains a documented future run, not a release claim.

### Phase 9: Final Production Gate

Status: Done.

Final release checklist:

- What works: local and GitHub ingestion paths, deterministic extraction, cited context packs, repo-scoped retrieval, license-aware citations, CLI, HTTP, MCP-compatible stdio, Reflexion feedback, backup/restore, doctor checks, and local benchmark reports.
- What was tested: compile, full unit/integration suite, Ruff, CLI status/doctor/retrieve/benchmark, HTTP contract smoke, MCP `tools/list` and `retrieve_context`, and bundled GraphRAG slice ingest/retrieval.
- Benchmark numbers: release index has 1 repository, 80 files, 297 symbols, 35 knowledge objects, 425 graph nodes, 791 graph edges, 5 benchmark tasks, 14 ms average retrieval latency, and 1.0 citation coverage.
- GraphRAG validation: 155-file slice, 455 symbols, 49 knowledge objects, 661 graph nodes, 1,102 graph edges; retrieval returned query context-builder files in the top results.
- Known limitations: no 20-repository or 100+ repository benchmark claim, scanner-based TypeScript extraction, JSON-RPC stdio MCP adapter instead of official SDK wrapper, and approximate word-count token budgeting.
- Release recommendation: ready for GitHub publication as v0.1.0 local MVP.

Commands run:

- `python3 -m compileall repo_wiki` passed.
- `python3 -m unittest discover -s tests -v` passed after progress was updated: 27 tests, 0 failures.
- `RUFF_CACHE_DIR=/tmp/repo-wiki-phase89-ruff-cache /tmp/repo-wiki-phase89-venv/bin/python -m ruff check .` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-phase89 python3 -m repo_wiki.interfaces.cli doctor` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-phase89 python3 -m repo_wiki.interfaces.cli status` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-phase89 python3 -m repo_wiki.interfaces.cli retrieve 'add regression tests for HTTP errors' --format json --limit 3` passed and returned `schema_version: context_pack.v1`.
- MCP `tools/list` smoke passed through `repo_wiki.interfaces.cli mcp serve`.
- MCP `retrieve_context` smoke passed through `repo_wiki.interfaces.cli mcp serve` and returned `schema_version: context_pack.v1`.
- `python3 -m unittest tests.test_end_to_end.EndToEndTest.test_phase3_interface_contracts_are_consistent -v` passed as the HTTP/API contract smoke.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-phase89-graphrag python3 -m repo_wiki.interfaces.cli ingest local dataset/graphrag-main --include 'packages/graphrag/graphrag/index/**' --include 'packages/graphrag/graphrag/query/**' --include 'tests/unit/query/**' --include 'README.md' --include 'pyproject.toml'` passed.
- `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-phase89-graphrag python3 -m repo_wiki.interfaces.cli retrieve 'how does GraphRAG build query context' --format json --limit 3` passed and returned context-builder paths.
- `git diff --check` passed.

Generated artifact hygiene:

- Runtime databases, Ruff cache, virtualenv, graph checks, and GraphRAG validation state stayed under `/tmp`.
- Source-tree Python caches generated by compile/tests were removed after final verification.
