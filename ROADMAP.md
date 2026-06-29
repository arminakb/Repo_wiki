# Production Readiness Roadmap

## Required First Task

1. Review the entire project in detail.

The next agent must complete this task before all other implementation, optimization, hardening, or publication work.

## Operating Instructions for the Next Agent

This roadmap is grounded in `SAS.md`, which is the source of truth for the Repo Knowledge Compiler. Execute phases sequentially. Do not skip a phase unless its acceptance criteria are already demonstrably satisfied.

After completing each phase, update `progress.md` before moving on. The update must include:

- A visual progress bar at the top of `progress.md`, for example `[████░░░░░░] 40%`.
- A brief phase report describing what was done, what changed, tests run, results, remaining risks, and links or paths to key files.
- The completed phase marked as done in the tracker.

Keep implementation aligned with the SAS principles: deterministic extraction before reasoning, cited knowledge only, graph-enhanced retrieval rather than graph-only retrieval, local-first storage, license/privacy metadata preservation, staged learning, thin interfaces over core services, and documentation as architecture.

## Current Baseline

The project already contains a substantial local-first Python implementation:

- Domain models in `repo_wiki/domain/`.
- Local and GitHub ingestion services.
- Deterministic extraction for file trees, Python, TypeScript/JavaScript, Markdown, routes, and package manifests.
- SQLite storage with FTS, graph tables, retrieval traces, context packs, feedback, and staged knowledge.
- Deterministic local vector scoring behind `repo_wiki/storage/vector.py`.
- Graph-enhanced retrieval and reranking.
- CLI, optional FastAPI app factory, stdlib HTTP server, and MCP-like JSON-RPC stdio adapter.
- End-to-end tests in `tests/test_end_to_end.py`.
- Architecture docs, ADRs, diagrams, examples, benchmark docs, README, `AGENT.md`, and `SAS.md`.

Known gaps to verify and close:

- The repository root was not detected as a Git repository during review, so GitHub publication hygiene and commit history are unresolved.
- CLI currently uses `argparse`, while SAS recommends Typer.
- HTTP has an optional FastAPI factory but also a stdlib server; decide whether to keep both or make FastAPI the primary production interface.
- MCP adapter is JSON-RPC stdio compatible but not clearly based on the official MCP SDK required by SAS.
- SQLite schema is created inline rather than through explicit versioned migration files.
- Configuration is environment-variable based; SAS calls for `repo-wiki.toml` or equivalent hardened config.
- Retrieval quality on a large real repository such as `dataset/graphrag-main/` needs deeper validation, relevance scoring, and benchmark evidence.
- Generated local state such as `.repo-wiki/`, caches, and report outputs must remain excluded and cleaned before publication.

## Phase 0: Full Project Review and Baseline

### Objective

Establish an exact understanding of the current codebase, architecture, implemented behavior, test status, and gap list before modifying production code.

### Tasks

1. Confirm completion of the required first task: Review the entire project in detail.
2. Read `SAS.md`, `AGENT.md`, `ARCHITECTURE.md`, `DECISIONS.md`, README, ADRs, docs, tests, and the main packages under `repo_wiki/`.
3. Produce a baseline inventory of implemented features against SAS functional requirements:
   - Ingestion: `FR-ING-*`.
   - Extraction: `FR-EXT-*`.
   - Knowledge compilation: `FR-KC-*`.
   - Retrieval: `FR-RET-*`.
   - Interfaces: `FR-IF-*`.
   - Reflexion: `FR-REF-*`.
   - Non-functional requirements: performance, reliability, security, maintainability, portfolio quality.
4. Run repository discovery commands:
   - `python3 -m compileall repo_wiki`
   - `python3 -m unittest discover -s tests -v`
   - `python3 -m repo_wiki.interfaces.cli doctor`
   - `python3 -m repo_wiki.interfaces.cli status`
5. Inspect generated artifact hygiene:
   - Ensure `.repo-wiki/`, `__pycache__/`, `.pytest_cache/`, benchmark databases, temporary reports, and local test outputs are absent or ignored.
   - Confirm real source tests under `tests/` are preserved.
6. Test the existing pipeline on a small fixture and on `dataset/graphrag-main/` using a temporary data directory outside tracked source.
7. Record concrete failures, weak behavior, missing requirements, and unclear architecture decisions in `progress.md`.

### Acceptance Criteria

- A written baseline report exists in `progress.md`.
- The report states whether compile and unit tests pass.
- The report lists all SAS requirement gaps found during review.
- The report identifies generated files that must not be committed.
- No implementation work begins before this phase is complete.

### Dependencies

- None.

## Phase 1: Issue Resolution - Runtime, Test, and Data Hygiene

### Objective

Fix current bugs, test failures, broken commands, generated artifact leakage, and immediate logical problems before optimization or feature hardening.

### Tasks

1. Fix all failures from:
   - `python3 -m compileall repo_wiki`
   - `python3 -m unittest discover -s tests -v`
   - CLI smoke commands.
   - HTTP smoke tests.
   - MCP JSON-RPC smoke tests.
2. Add or update `.gitignore` so local/generated artifacts are excluded:
   - `.repo-wiki/`
   - `__pycache__/`
   - `.pytest_cache/`
   - `.ruff_cache/`
   - `.mypy_cache/`
   - local SQLite databases
   - benchmark output databases
   - temporary reports
   - virtual environments
3. Remove generated artifacts from the working tree without deleting source tests, docs, or dataset fixtures.
4. Fix local data directory handling so commands do not accidentally index or publish generated `.repo-wiki/` contents.
5. Verify all CLI commands in README either work or are explicitly marked as planned.
6. Fix command output inconsistencies that break scripted validation.
7. Add regression tests for any discovered bug.
8. Validate that indexed repository code is never executed.

### Acceptance Criteria

- Compile and unit tests pass locally.
- Smoke commands return success or clear expected errors.
- Generated local state is ignored and not required for a clean run.
- No real test files or fixtures are removed.
- `progress.md` contains a phase report and updated progress bar.

### Dependencies

- Phase 0 complete.

## Phase 2: Issue Resolution - SAS Core Contract Gaps

### Objective

Close functional gaps in the core engine so the project satisfies the SAS Version 1 core requirements.

### Tasks

1. Audit ingestion against `FR-ING-*`:
   - Public GitHub URL ingestion.
   - Local path ingestion.
   - repository metadata.
   - include/exclude patterns.
   - generated/dependency directory skipping.
   - file hashes and snapshot hashes.
   - license and privacy metadata.
2. Fix ingestion restartability gaps:
   - Make repeated indexing idempotent.
   - Ensure failed files are logged and skipped when safe.
   - Preserve snapshot status and metrics.
3. Audit extraction against `FR-EXT-*`:
   - Python modules, imports, classes, functions, methods, docstrings, call references.
   - TypeScript/JavaScript imports, exports, functions, classes, interfaces, React components, route files, package usage.
   - package manifests.
   - test-to-source relationships.
   - Markdown headings, code fences, links, hierarchy.
   - extraction events and metrics.
4. Improve missing or weak extractors only where they affect SAS acceptance:
   - Add tests for line-specific citations.
   - Add tests for route detection.
   - Add tests for test-to-source linking.
   - Add tests for TypeScript and Markdown edge cases.
5. Audit knowledge compilation against `FR-KC-*`:
   - ProjectProfile.
   - ArchitecturePattern.
   - ImplementationPattern.
   - TestingPattern.
   - AntiPattern.
   - source references.
   - Pydantic validation.
   - deduplication.
6. Add missing knowledge object types or explicitly document why a type is deferred.
7. Ensure every stored knowledge object has at least one valid `SourceRef`.
8. Ensure snippet policy is enforced before any code-like source content is returned.

### Acceptance Criteria

- Local and GitHub ingestion satisfy the SAS acceptance gate in a reproducible smoke test.
- Extraction creates cited artifacts for Python, TypeScript/JavaScript, Markdown, dependencies, routes, and tests.
- Knowledge objects are typed, validated, cited, deduplicated, and scored.
- Regression tests cover the core gaps fixed.
- `progress.md` contains a phase report and updated progress bar.

### Dependencies

- Phase 1 complete.

## Phase 3: Issue Resolution - Interface Contract Completion

### Objective

Ensure CLI, HTTP API, and MCP expose the same core behavior and match the SAS public contracts.

### Tasks

1. Audit CLI against SAS section 20:
   - `init`
   - `ingest github`
   - `ingest local`
   - `retrieve` and `query`
   - `knowledge list/show`
   - `graph neighbors/export`
   - `feedback submit/list/promote/reject`
   - `metrics`
   - `benchmark run/ingest-list/report`
   - `api serve`
   - `mcp serve`
2. Decide whether to migrate from `argparse` to Typer now or document and defer it with an ADR. If migrated, preserve command compatibility.
3. Audit HTTP API against SAS section 19:
   - `GET /health`
   - `POST /v1/ingest/repository`
   - `POST /v1/ingest/local`
   - `GET /v1/repositories/{repo_id}`
   - `GET /v1/knowledge`
   - `POST /v1/retrieve`
   - `POST /v1/feedback`
   - `GET /v1/metrics`
4. Make FastAPI the production path or document the stdlib server as a fallback. If keeping both, tests must cover both.
5. Add request/response validation using Pydantic models for HTTP payloads.
6. Audit MCP against SAS section 21:
   - `retrieve_context`
   - `search_knowledge`
   - `inspect_repository`
   - `submit_feedback`
   - repository, knowledge, context pack, and metrics resources.
7. Decide whether to use the official MCP SDK now or document and defer with an ADR. If implemented, keep the adapter thin.
8. Ensure all interfaces call core services and do not duplicate business logic.
9. Add interface contract tests and docs examples for CLI, HTTP, and MCP.

### Acceptance Criteria

- CLI, HTTP, and MCP return consistent context pack shapes.
- Interface tests cover happy paths and key error paths.
- Public docs examples execute successfully.
- Any deviation from SAS tool recommendations is covered by an ADR.
- `progress.md` contains a phase report and updated progress bar.

### Dependencies

- Phase 2 complete.

## Phase 4: Optimization - Retrieval Quality and Pipeline Performance

### Objective

Improve usefulness, relevance, latency, and maintainability of the retrieval pipeline without changing the product scope.

### Tasks

1. Create a fixed retrieval quality suite based on SAS section 31:
   - backend tasks.
   - frontend tasks.
   - testing tasks.
   - refactor tasks.
   - bug-fix tasks.
2. Include `dataset/graphrag-main/` as a real-world stress repository.
3. Measure baseline:
   - indexing time.
   - indexed files.
   - skipped files.
   - symbols.
   - dependencies.
   - knowledge objects.
   - graph nodes and edges.
   - retrieval latency.
   - citation coverage.
   - top-k relevance.
4. Improve retrieval where evidence shows weakness:
   - lexical query normalization.
   - deterministic vector text construction.
   - metadata filtering.
   - bounded graph expansion.
   - reranking weights.
   - context compression.
   - duplicate removal.
5. Enforce token budgets more accurately.
6. Ensure retrieval traces include candidate counts, latency, filters, retrievers used, and ranking details.
7. Add golden tests for context pack shape and citation behavior.
8. Add performance tests with reasonable thresholds for small and medium indexes.
9. Keep all scoring explainable in returned context or trace metadata.

### Acceptance Criteria

- Retrieval returns useful cited context packs for representative Python and TypeScript tasks.
- Small-index retrieval target is under 2 seconds.
- Larger MVP-index retrieval target is under 5 seconds or documented with measured bottlenecks.
- Context packs include recommendations, examples, architecture rules, tests, risks, citations, and trace IDs.
- Quality suite and benchmark report are reproducible.
- `progress.md` contains a phase report and updated progress bar.

### Dependencies

- Phase 3 complete.

## Phase 5: Optimization - Code Structure, Maintainability, and Storage

### Objective

Refactor only where it reduces real complexity, strengthens boundaries, or supports production operation.

### Tasks

1. Audit module boundaries against SAS section 22:
   - `interfaces -> core -> domain`
   - storage owns SQL.
   - extractors own parsing.
   - retrieval owns planning, ranking, and context generation.
   - graph owns graph operations.
   - reflexion owns feedback/staging/promotion.
2. Remove circular dependencies and duplicate logic if found.
3. Split oversized modules only when it improves testability or aligns with existing architecture.
4. Add explicit storage migrations:
   - migration version table.
   - migration files or lightweight migration runner.
   - tests for fresh database creation and upgrade.
5. Review SQL indexes and add only those justified by measured queries.
6. Harden SQLite writes:
   - transactional multi-table writes.
   - clear error handling.
   - integrity checks.
7. Add `repo-wiki.toml` support or equivalent config loader:
   - storage paths.
   - max file size.
   - default excludes.
   - license policy.
   - retrieval limits.
   - LLM provider disabled by default.
8. Keep environment variables as overrides if useful.
9. Add typed configuration tests.
10. Update ADRs if storage, config, vector, MCP, or interface decisions change.

### Acceptance Criteria

- Core business logic remains independent from CLI/HTTP/MCP.
- Database schema is explicitly versioned.
- Config is reproducible, documented, and test-covered.
- Refactors do not change public behavior without tests and docs.
- `progress.md` contains a phase report and updated progress bar.

### Dependencies

- Phase 4 complete.

## Phase 6: Production Readiness - Reliability, Security, and Error Handling

### Objective

Make the project robust enough for real local production-style usage and safe handling of untrusted repositories.

### Tasks

1. Implement or complete domain errors from SAS section 37:
   - `RepositoryNotFound`.
   - `UnsupportedSource`.
   - `LicensePolicyViolation`.
   - `ExtractionFailed`.
   - `KnowledgeValidationFailed`.
   - `RetrievalFailed`.
   - `StorageError`.
   - `MCPValidationError`.
2. Map errors cleanly:
   - readable CLI messages and nonzero exit codes.
   - HTTP status codes and JSON error bodies.
   - MCP tool errors.
3. Add structured logging for:
   - ingestion start/end.
   - extraction failures.
   - compiler validation failures.
   - retrieval traces.
   - API requests.
   - MCP tool calls.
   - feedback events.
4. Add security hardening:
   - path traversal prevention.
   - max file size enforcement.
   - binary file skipping.
   - secret redaction tests.
   - `.env` and private key exclusion.
   - no execution/import of indexed code.
5. Enforce license policy:
   - permissive-only snippets.
   - metadata-only mode.
   - allow-all-public warnings.
   - private-local-only behavior.
6. Add backup and restore if still needed for production maturity:
   - `repo-wiki backup create`
   - `repo-wiki backup restore`
   - tests for backup integrity.
7. Add health and doctor checks for storage, git, config, and optional dependencies.

### Acceptance Criteria

- Interfaces handle expected failures gracefully.
- Security tests cover untrusted repository content and secrets.
- License policy is enforced in retrieval outputs.
- Logs and metrics are sufficient to debug ingestion and retrieval failures.
- `progress.md` contains a phase report and updated progress bar.

### Dependencies

- Phase 5 complete.

## Phase 7: Production Readiness - Test Matrix, CI, and Real Environment Validation

### Objective

Prove the project works in a realistic environment with repeatable test, benchmark, and documentation validation.

### Tasks

1. Build a test matrix:
   - unit tests for models, IDs, filters, parsers, scoring, dedupe, reranking, context pack generation.
   - integration tests for SQLite, ingestion, retrieval, graph, feedback, CLI, HTTP, MCP.
   - golden tests for context packs.
   - benchmark tests for retrieval quality and latency.
2. Add CI workflow:
   - formatting check.
   - linting.
   - type checking if configured.
   - unit and integration tests.
   - docs/link smoke checks where practical.
3. Add developer commands to README and docs:
   - install.
   - run tests.
   - run lint.
   - run API.
   - run MCP.
   - run benchmark.
4. Validate local real-environment flow:
   - create a clean temporary data dir.
   - initialize storage.
   - ingest a local sample repo.
   - ingest `dataset/graphrag-main/`.
   - retrieve context for multiple tasks.
   - submit feedback.
   - promote/reject staged knowledge.
   - export graph.
   - generate benchmark report.
5. Record benchmark metrics in `docs/benchmarks/mvp-results.md` only from actual commands.
6. Confirm installability:
   - editable install.
   - console script `repo-wiki`.
   - clean run from outside repository root.
7. Validate docs examples by executing all documented commands or marking commands as planned.

### Acceptance Criteria

- CI passes from a clean checkout.
- Local real-environment validation is documented with exact commands and results.
- Benchmark metrics are real and reproducible.
- Docs examples match current behavior.
- `progress.md` contains a phase report and updated progress bar.

### Dependencies

- Phase 6 complete.

## Phase 8: Publication - GitHub Repository Preparation

### Objective

Prepare the project for final public review and GitHub release.

### Tasks

1. Confirm repository state:
   - initialize or repair Git repository if needed.
   - verify root is correct.
   - inspect tracked/untracked files.
   - ensure generated artifacts are not staged.
2. Finalize top-level project files:
   - `README.md`.
   - `LICENSE`.
   - `CONTRIBUTING.md`.
   - `AGENT.md`.
   - `ARCHITECTURE.md`.
   - `SAS.md`.
   - `ROADMAP.md`.
   - `DECISIONS.md`.
   - `.gitignore`.
   - `.env.example` if configuration requires it.
   - `pyproject.toml`.
3. Update README with production-quality content:
   - product explanation.
   - architecture diagram.
   - quickstart.
   - supported languages.
   - supported interfaces.
   - CLI example.
   - HTTP example.
   - MCP example.
   - real benchmark metrics.
   - roadmap link.
   - docs links.
4. Finalize docs:
   - architecture docs.
   - ADRs.
   - diagrams.
   - benchmark methodology and results.
   - examples.
   - setup/testing docs.
   - API and MCP docs.
5. Confirm license compatibility for included code and datasets.
6. Add release notes or changelog for first public version.
7. Ensure conventional commit history for final work.
8. Tag a release only after all tests, docs, and benchmark checks pass.

### Acceptance Criteria

- Clean Git status except intentional release files.
- README is accurate and demo-ready.
- License and contribution guidance are present.
- `.gitignore` prevents generated artifacts from publication.
- Release notes summarize features, limitations, and known follow-up work.
- `progress.md` contains a phase report and updated progress bar.

### Dependencies

- Phase 7 complete.

## Phase 9: Final Production Gate

### Objective

Make a final go/no-go decision for a polished production-grade GitHub release.

### Tasks

1. Run final commands from a clean environment:
   - `python3 -m compileall repo_wiki`
   - `python3 -m unittest discover -s tests -v`
   - lint command selected by the project.
   - type check command if configured.
   - CLI smoke test.
   - HTTP smoke test.
   - MCP smoke test.
   - benchmark report generation.
2. Re-run a real repository validation on `dataset/graphrag-main/`.
3. Verify no source-derived large snippets are returned in context packs.
4. Verify generated artifacts are ignored or removed.
5. Verify `progress.md` is complete and includes all phase reports.
6. Produce a final release checklist in `progress.md`:
   - what works.
   - what was tested.
   - benchmark numbers.
   - known limitations.
   - release recommendation.

### Acceptance Criteria

- All critical tests pass.
- All docs are current.
- Real-environment validation succeeds.
- No generated test artifacts are staged for release.
- Project is ready for GitHub publication or has a clearly documented blocker.
- `progress.md` shows `[██████████] 100%`.

### Dependencies

- Phase 8 complete.

## Cross-Phase Rules

- Do not execute indexed repository code.
- Do not add cloud services, Neo4j, SaaS features, browser UI, or distributed workers for Version 1.
- Do not introduce a major dependency without an ADR or decision update.
- Keep generated local state out of source control.
- Keep tests close to the behavior they protect.
- Every behavior change must be covered by tests or an explicit rationale.
- Every architecture change must update docs and ADRs.
- Every context pack must remain compact, cited, and license-aware.
