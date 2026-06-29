# Software Architecture Specification: Repo Knowledge Compiler

Status: Draft v1
Audience: autonomous coding agents, maintainers, reviewers, portfolio evaluators
Primary implementation mode: local-first, agent-friendly, documentation-first
Primary source of truth: this document

## 1. Executive Summary

Repo Knowledge Compiler is a local-first system that indexes software repositories and turns them into structured, cited implementation knowledge for coding agents. It is not a general chatbot and it is not only a graph database. It is a knowledge compiler, retrieval planner, and context pack generator designed to help coding agents write cleaner, more consistent code inside real projects.

The system ingests public GitHub repositories first, focusing on Python and TypeScript/JavaScript. It extracts deterministic code intelligence from source files, documentation, dependency manifests, routes, tests, schemas, and configuration files. It then compiles high-signal knowledge objects such as architecture summaries, implementation patterns, module patterns, testing patterns, security patterns, code examples, constraints, tradeoffs, and anti-patterns.

The first production-quality version exposes three interfaces:

- CLI for local workflows and demos.
- HTTP API for service integration and benchmark automation.
- MCP server for modern agent ecosystems.

The storage design starts with SQLite, SQLite FTS5, a local vector index, and a lightweight knowledge graph table model. The graph is useful, but it is used as a structured relationship layer over compiled knowledge, not as the only retrieval mechanism. Retrieval combines lexical search, metadata filtering, vector search, graph expansion, reranking, and context compression.

The repository itself must be designed as a professional portfolio project. Documentation, diagrams, ADRs, benchmark reports, usage examples, roadmap, clean commits, and agent-facing project files are first-class deliverables.

## 2. Product Vision

The long-term vision is to build an LLM wiki for repositories and projects: a system that reads many real codebases, extracts reusable implementation knowledge, and gives coding agents concise, cited, task-specific guidance.

The system should answer questions like:

- What architectural patterns does this repository use?
- How do real projects implement a feature similar to this task?
- Which files, modules, tests, and dependencies are relevant?
- What conventions should an agent follow before editing this repo?
- What examples from indexed repositories are safe and useful?
- What risks, anti-patterns, and test cases should the agent consider?

The system should produce context packs that a coding agent can directly consume before making edits.

## 3. Objectives

### 3.1 Primary Objectives

1. Ingest GitHub repositories and local repositories into a structured local knowledge store.
2. Extract deterministic code intelligence before using any LLM reasoning.
3. Compile repository data into typed, cited knowledge objects.
4. Build a knowledge graph of useful relationships between repos, files, symbols, patterns, tests, dependencies, frameworks, and examples.
5. Provide hybrid retrieval that returns compact, cited context packs for coding tasks.
6. Expose the core through CLI, HTTP API, and MCP server in Version 1.
7. Include Reflexion-style feedback and staging so accepted implementations can improve the knowledge base without polluting it.
8. Treat documentation, diagrams, ADRs, examples, and benchmarks as product features.

### 3.2 Non-Objectives

The MVP will not:

- Build a general-purpose chat assistant.
- Crawl the entire public GitHub ecosystem.
- Depend on Neo4j or a distributed graph database.
- Guarantee legal reuse of arbitrary code snippets.
- Generate large code blocks copied from indexed repositories.
- Replace project-specific human review.
- Support every programming language.
- Require cloud infrastructure.
- Require a specific external LLM vendor.

## 4. Target Users

### 4.1 Primary Users

- Developers using coding agents.
- AI engineer candidates showing an advanced portfolio project.
- Maintainers who want an agent-readable knowledge layer over repositories.
- Researchers evaluating repository-level retrieval for code generation.

### 4.2 Primary Agent Users

- Codex-style coding agents.
- Claude Code-style local coding agents.
- OpenHands-style autonomous software agents.
- IDE-integrated agents using MCP.
- Internal agent workflows that need cited implementation context.

## 5. System Boundaries

### 5.1 In Scope

- Public GitHub repository ingestion.
- Local repository ingestion.
- Python and TypeScript/JavaScript parsing.
- README and Markdown documentation parsing.
- Package/dependency detection.
- Basic route/API detection for common frameworks.
- Test-to-source relationship detection.
- Knowledge object generation.
- SQLite metadata store.
- SQLite FTS5 lexical index.
- Local vector index.
- Lightweight graph tables in SQLite.
- CLI.
- HTTP API.
- MCP server.
- Benchmarking tools.
- Documentation site structure.
- ADRs and diagrams.
- Reflexion staging and scoring.

### 5.2 Out of Scope for MVP

- Multi-tenant SaaS.
- Billing, accounts, teams, or permissions.
- Full private repository governance.
- Distributed ingestion workers.
- Large-scale hosted vector databases.
- Neo4j.
- Browser UI.
- IDE plugin.
- Fine-tuning models.
- Automatic code modification.

### 5.3 Hard Boundaries

The system returns context. It does not directly apply code edits in target repositories.

The system can cite source files and provide short examples when allowed. It must not generate large copied code from indexed repositories.

The system must keep license and privacy metadata attached to every source and derived object.

## 6. Architectural Principles

1. Deterministic extraction before reasoning.
   Parsers, AST tools, dependency analyzers, and metadata extraction run before LLM-based transformation.

2. Cited knowledge only.
   Every knowledge object derived from source material must preserve traceable source references.

3. Graph-enhanced, not graph-only.
   Graph relationships are valuable for expansion and explanation, but retrieval starts with hybrid search and metadata filtering.

4. Local-first by default.
   The MVP must run on a developer machine with local storage.

5. Interface separation.
   Core engine logic must be independent from CLI, HTTP, and MCP adapters.

6. License and privacy first.
   Ingestion must capture license, visibility, source origin, and snippet policy before extraction output becomes retrievable.

7. Staged learning.
   Feedback and accepted implementations go to staging before promotion to the main knowledge store.

8. Documentation as architecture.
   Docs, diagrams, ADRs, benchmarks, examples, and roadmap evolve with code.

9. Agent-friendly repository.
   AGENT.md, ARCHITECTURE.md, ROADMAP.md, DECISIONS.md, CONTRIBUTING.md, examples, and API docs must be present from day one.

10. Measurable progress.
   The project should expose metrics such as indexed repos, extracted patterns, knowledge nodes, context pack quality, retrieval latency, and citation correctness.

## 7. Core Concepts and Terminology

### 7.1 Source

A source is an origin of data. Examples:

- GitHub repository.
- Local repository.
- Markdown docs folder.
- OpenAPI spec.
- Database schema file.
- Accepted implementation produced by an agent.

### 7.2 Repository Snapshot

A repository snapshot is a specific indexed state of a repository, identified by commit SHA or local snapshot hash.

### 7.3 Artifact

An artifact is a raw or parsed item extracted from a source:

- Source file.
- README file.
- Symbol.
- Function.
- Class.
- Module.
- Route.
- API endpoint.
- Test case.
- Dependency.
- Configuration file.

### 7.4 Knowledge Object

A knowledge object is a structured, reusable unit compiled from artifacts:

- ProjectProfile.
- ArchitecturePattern.
- ImplementationPattern.
- ModulePattern.
- FunctionPattern.
- ClassPattern.
- APIEndpointPattern.
- DatabasePattern.
- AgentWorkflowPattern.
- TestingPattern.
- SecurityPattern.
- AntiPattern.
- DecisionRecord.
- CodeExample.
- Constraint.
- Tradeoff.

### 7.5 Knowledge Node

A knowledge node is any graph-addressable object. Artifacts and knowledge objects can both become nodes.

### 7.6 Knowledge Edge

A knowledge edge is a typed relationship between nodes, such as IMPLEMENTS, TESTED_BY, IMPORTS, CALLS, USES_PATTERN, DERIVED_FROM, or APPLIES_TO_FRAMEWORK.

### 7.7 Context Pack

A context pack is a compact, cited output produced for an agent task. It contains relevant patterns, examples, architecture rules, implementation steps, tests, risks, and source citations.

### 7.8 Reflexion Record

A Reflexion record is feedback captured after an agent uses retrieved context. It includes task metadata, retrieved context, final outcome, tests, human rating, accepted code references, and promotion status.

### 7.9 Staging Knowledge

Staging knowledge is extracted from new agent outputs or feedback but not yet promoted to the main knowledge store.

## 8. Functional Requirements

### 8.1 Ingestion Requirements

FR-ING-001: The system shall ingest a public GitHub repository by URL.

FR-ING-002: The system shall ingest a local repository path.

FR-ING-003: The system shall record repository metadata including owner, name, URL, default branch, commit SHA, license, visibility, primary language, detected frameworks, stars when available, and indexed timestamp.

FR-ING-004: The system shall support include and exclude patterns.

FR-ING-005: The system shall avoid indexing common generated or dependency directories by default, including node_modules, .git, dist, build, .next, vendor, coverage, and virtual environments.

FR-ING-006: The system shall compute file hashes to support incremental re-indexing.

FR-ING-007: The system shall record license and privacy policy before making source-derived snippets retrievable.

### 8.2 Extraction Requirements

FR-EXT-001: The system shall extract file tree metadata.

FR-EXT-002: The system shall extract Python modules, imports, classes, functions, methods, docstrings, and basic call references.

FR-EXT-003: The system shall extract TypeScript/JavaScript imports, exports, functions, classes, interfaces, React components, route files, and package usage.

FR-EXT-004: The system shall parse package manifests such as package.json, pyproject.toml, requirements.txt, setup.py, pnpm-lock.yaml, yarn.lock, package-lock.json, and poetry.lock when present.

FR-EXT-005: The system shall detect tests and link tests to likely implementation files using naming conventions, imports, and path similarity.

FR-EXT-006: The system shall parse Markdown docs and preserve headings, code fences, links, and document hierarchy.

FR-EXT-007: The system shall emit extraction events and metrics.

### 8.3 Knowledge Compilation Requirements

FR-KC-001: The system shall generate ProjectProfile objects for indexed repos.

FR-KC-002: The system shall generate ArchitecturePattern objects when architectural conventions can be inferred.

FR-KC-003: The system shall generate ImplementationPattern objects for reusable feature or module implementations.

FR-KC-004: The system shall generate TestingPattern objects for meaningful test approaches.

FR-KC-005: The system shall generate AntiPattern objects for detectable risky or inconsistent implementation choices.

FR-KC-006: The system shall attach source references to every knowledge object.

FR-KC-007: The system shall validate knowledge objects with Pydantic schemas before storage.

FR-KC-008: The system shall deduplicate highly similar patterns.

### 8.4 Retrieval Requirements

FR-RET-001: The system shall accept a natural-language coding task.

FR-RET-002: The system shall accept optional filters such as language, framework, domain, repo, license policy, and max tokens.

FR-RET-003: The system shall classify task type.

FR-RET-004: The system shall retrieve candidates using SQLite FTS5.

FR-RET-005: The system shall retrieve candidates using local vector search when embeddings are available.

FR-RET-006: The system shall expand candidates through graph edges.

FR-RET-007: The system shall rerank candidates.

FR-RET-008: The system shall compile a compact JSON and Markdown context pack.

FR-RET-009: The system shall include citations for all recommendations.

FR-RET-010: The system shall record retrieval logs for evaluation.

### 8.5 Interface Requirements

FR-IF-001: The system shall expose a CLI.

FR-IF-002: The system shall expose a FastAPI HTTP API.

FR-IF-003: The system shall expose an MCP server in Version 1.

FR-IF-004: The CLI, HTTP API, and MCP server shall call the same core services.

### 8.6 Reflexion Requirements

FR-REF-001: The system shall record feedback for a retrieved context pack.

FR-REF-002: The system shall record objective signals including tests passed, lint passed, build passed, merge status, reviewer approval, rollback, and incident flags when provided.

FR-REF-003: The system shall store new candidate knowledge in staging.

FR-REF-004: The system shall require scoring and deduplication before promotion.

FR-REF-005: The system shall keep provenance from staged knowledge to final promoted objects.

## 9. Non-Functional Requirements

### 9.1 Performance

NFR-PERF-001: Indexing a medium repository under 10,000 files should complete locally in minutes, not hours.

NFR-PERF-002: Retrieval should return a context pack in under 2 seconds for small local indexes and under 5 seconds for larger MVP indexes.

NFR-PERF-003: The system should support at least 100 indexed repositories in the MVP benchmark.

NFR-PERF-004: The architecture should have a credible path to 100,000 repositories.

### 9.2 Reliability

NFR-REL-001: Ingestion should be restartable.

NFR-REL-002: Failed files should be logged and skipped without failing the entire repo unless a critical metadata step fails.

NFR-REL-003: Storage writes should be transactional.

NFR-REL-004: Schema migrations should be explicit and versioned.

### 9.3 Security and Compliance

NFR-SEC-001: The system must not execute indexed repository code.

NFR-SEC-002: The system must treat repository content as untrusted input.

NFR-SEC-003: The system must store license metadata.

NFR-SEC-004: The system must apply snippet policy before returning source-derived code examples.

NFR-SEC-005: Private repository support must default to privacy-preserving local storage and no external LLM calls unless explicitly configured.

### 9.4 Maintainability

NFR-MAINT-001: Core services must be independent from interface adapters.

NFR-MAINT-002: Data schemas must be typed and validated.

NFR-MAINT-003: Tests must cover parsers, storage, retrieval, context pack generation, and interface contracts.

NFR-MAINT-004: Docs and ADRs must be updated when architecture changes.

### 9.5 Portfolio Quality

NFR-PORT-001: The repository must include professional README, architecture diagrams, ADRs, roadmap, usage examples, benchmark results, and design decision documentation.

NFR-PORT-002: Commit history should use conventional, descriptive commit messages.

NFR-PORT-003: Public project metrics should be visible in README and benchmark docs.

## 10. High-Level Architecture

```text
                       +--------------------------+
                       | Source Intake            |
                       | GitHub / Local Repos     |
                       +------------+-------------+
                                    |
                       +------------v-------------+
                       | Validation + Metadata    |
                       | license, privacy, tech   |
                       +------------+-------------+
                                    |
                       +------------v-------------+
                       | Deterministic Extraction |
                       | AST, symbols, docs, deps |
                       +------------+-------------+
                                    |
                       +------------v-------------+
                       | Knowledge Compiler       |
                       | typed objects + citations|
                       +------------+-------------+
                                    |
              +---------------------+---------------------+
              |                     |                     |
              v                     v                     v
   +--------------------+ +--------------------+ +--------------------+
   | Metadata Store     | | Lexical Index      | | Vector Index       |
   | SQLite             | | SQLite FTS5        | | local embeddings   |
   +--------------------+ +--------------------+ +--------------------+
              |                     |                     |
              +---------------------+---------------------+
                                    |
                       +------------v-------------+
                       | Graph Relationship Layer |
                       | nodes + typed edges      |
                       +------------+-------------+
                                    |
                       +------------v-------------+
                       | Retrieval Planner        |
                       | classify, filter, rank   |
                       +------------+-------------+
                                    |
                       +------------v-------------+
                       | Context Pack Generator   |
                       | JSON + Markdown + cites  |
                       +------------+-------------+
                                    |
              +---------------------+---------------------+
              |                     |                     |
              v                     v                     v
        +-----------+         +-----------+          +-----------+
        | CLI       |         | HTTP API  |          | MCP Server|
        +-----------+         +-----------+          +-----------+
                                    |
                       +------------v-------------+
                       | Reflexion + Learning     |
                       | feedback, staging, score |
                       +--------------------------+
```

## 11. Component Architecture

### 11.1 Core Engine

The core engine owns all business logic. Interface layers must not duplicate logic.

Core services:

- IngestionService.
- MetadataService.
- ExtractionService.
- KnowledgeCompilerService.
- GraphService.
- RetrievalService.
- ContextPackService.
- ReflexionService.
- BenchmarkService.

### 11.2 Source Intake

Responsibilities:

- Clone or open repositories.
- Resolve commit SHA.
- Apply include/exclude filters.
- Collect source metadata.
- Create repository snapshot record.
- Provide file iterator to extraction.

GitHub ingestion should use shallow clone by default. The system may also support GitHub archive downloads later.

### 11.3 Metadata and Validation

Responsibilities:

- Detect license.
- Detect language distribution.
- Detect frameworks.
- Detect privacy level.
- Apply snippet policy.
- Decide whether source can be indexed, summarized, embedded, or quoted.

License policy must be configurable:

- permissive_only: allow MIT, Apache-2.0, BSD, ISC.
- metadata_only: store metadata and derived summaries, no snippets.
- allow_all_public: allow all public repos but retain license warnings.
- private_local_only: private repos remain local and are not sent to external APIs.

### 11.4 Deterministic Extraction

Responsibilities:

- Parse file tree.
- Extract symbols.
- Extract imports/exports.
- Extract dependency manifests.
- Extract docs.
- Detect tests.
- Detect routes.
- Detect config.
- Emit artifacts and graph edges.

Recommended tools:

- tree-sitter for multi-language parsing.
- Python ast module for Python-specific extraction.
- ts-morph or TypeScript compiler API for TypeScript/JavaScript.
- markdown-it-py or mistune for Markdown.
- packaging/tomllib for Python package metadata.
- pydantic for validation.

### 11.5 Knowledge Compiler

Responsibilities:

- Convert artifacts into knowledge objects.
- Generate summaries and patterns.
- Attach citations.
- Validate schema.
- Score object quality.
- Deduplicate similar objects.
- Store accepted objects.

The compiler should run in two modes:

- deterministic-only mode, for tests and no-LLM environments.
- LLM-assisted mode, for richer summaries and pattern extraction.

### 11.6 Graph Service

Responsibilities:

- Store nodes and edges.
- Query neighbors by edge type.
- Expand retrieval candidates.
- Explain relationships in context packs.
- Support graph metrics for docs and benchmarks.

The graph layer should use SQLite tables in the MVP. NetworkX may be used in-process for algorithms and visualization exports.

### 11.7 Retrieval Planner

Responsibilities:

- Classify task.
- Extract constraints.
- Select retrievers.
- Retrieve lexical candidates.
- Retrieve vector candidates.
- Expand through graph.
- Filter by metadata/license/quality.
- Rerank.
- Build retrieval trace.

### 11.8 Context Pack Generator

Responsibilities:

- Convert ranked knowledge into agent-ready context.
- Enforce max token budget.
- Group by relevance.
- Include citations.
- Include implementation guidance.
- Include test suggestions.
- Include risks.
- Return JSON and Markdown.

### 11.9 Reflexion Service

Responsibilities:

- Record context usage.
- Record task outcome.
- Analyze final implementation metadata.
- Extract candidate new knowledge.
- Score and deduplicate staged knowledge.
- Promote staged knowledge when criteria are met.

### 11.10 Interfaces

The system exposes:

- CLI using Typer.
- HTTP API using FastAPI.
- MCP server using Python MCP SDK or TypeScript MCP SDK depending on final implementation choice.

Interfaces must import and call core services.

## 12. Data Model

### 12.1 Naming Conventions

- IDs use stable prefixes.
- Database primary keys are text UUIDs or deterministic content IDs.
- Timestamps use UTC ISO 8601.
- JSON fields are validated at service boundaries.

### 12.2 Repository

```json
{
  "id": "repo_01h...",
  "source_type": "github_repo",
  "owner": "example",
  "name": "project",
  "url": "https://github.com/example/project",
  "default_branch": "main",
  "visibility": "public",
  "license": "MIT",
  "primary_language": "TypeScript",
  "detected_languages": {
    "TypeScript": 0.72,
    "JavaScript": 0.18,
    "CSS": 0.10
  },
  "detected_frameworks": ["Next.js", "Prisma"],
  "stars": 1200,
  "quality_score": 0.82,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

### 12.3 RepositorySnapshot

```json
{
  "id": "snap_01h...",
  "repo_id": "repo_01h...",
  "commit_sha": "abc123",
  "branch": "main",
  "indexed_at": "2026-01-01T00:00:00Z",
  "file_count": 450,
  "line_count": 62000,
  "content_hash": "sha256:...",
  "status": "completed"
}
```

### 12.4 SourceFile

```json
{
  "id": "file_01h...",
  "snapshot_id": "snap_01h...",
  "path": "src/auth/reset.ts",
  "language": "TypeScript",
  "mime_type": "text/typescript",
  "size_bytes": 3400,
  "line_count": 120,
  "hash": "sha256:...",
  "is_test": false,
  "is_generated": false,
  "is_dependency": false
}
```

### 12.5 Symbol

```json
{
  "id": "sym_01h...",
  "file_id": "file_01h...",
  "snapshot_id": "snap_01h...",
  "name": "resetPassword",
  "kind": "function",
  "qualified_name": "src/auth/reset.ts::resetPassword",
  "start_line": 22,
  "end_line": 94,
  "signature": "async function resetPassword(input: ResetPasswordInput)",
  "docstring": null,
  "visibility": "exported"
}
```

### 12.6 Dependency

```json
{
  "id": "dep_01h...",
  "snapshot_id": "snap_01h...",
  "manager": "npm",
  "name": "next",
  "version_spec": "^15.0.0",
  "scope": "runtime",
  "manifest_path": "package.json"
}
```

### 12.7 SourceRef

```json
{
  "id": "ref_01h...",
  "repo_id": "repo_01h...",
  "snapshot_id": "snap_01h...",
  "file_id": "file_01h...",
  "path": "src/auth/reset.ts",
  "start_line": 22,
  "end_line": 94,
  "license": "MIT",
  "snippet_allowed": true
}
```

### 12.8 KnowledgeObject Base

```json
{
  "id": "ko_01h...",
  "type": "ImplementationPattern",
  "title": "Password reset with server actions",
  "summary": "Implements reset token validation and password update through a server action.",
  "problem": "Users need a secure way to reset credentials.",
  "solution": "Validate signed token, hash new password, update user, invalidate token.",
  "when_to_use": ["Next.js App Router", "email/password auth"],
  "when_not_to_use": ["external auth provider handles reset"],
  "language": "TypeScript",
  "frameworks": ["Next.js", "Prisma"],
  "domain": "auth",
  "tags": ["auth", "password-reset", "server-actions"],
  "quality_score": 0.82,
  "confidence": 0.76,
  "source_refs": ["ref_01h..."],
  "created_at": "2026-01-01T00:00:00Z"
}
```

### 12.9 ContextPack

```json
{
  "id": "ctx_01h...",
  "task": "implement password reset in Next.js with Prisma",
  "task_type": "backend_feature",
  "constraints": {
    "language": "TypeScript",
    "framework": "Next.js",
    "domain": "auth",
    "max_tokens": 4000
  },
  "recommended_patterns": [],
  "relevant_examples": [],
  "architecture_rules": [],
  "implementation_steps": [],
  "tests_to_consider": [],
  "risks": [],
  "source_citations": [],
  "retrieval_trace_id": "trace_01h..."
}
```

### 12.10 RetrievalTrace

```json
{
  "id": "trace_01h...",
  "task": "implement password reset",
  "created_at": "2026-01-01T00:00:00Z",
  "retrievers_used": ["fts", "vector", "graph"],
  "candidate_count": 120,
  "reranked_count": 20,
  "returned_count": 8,
  "latency_ms": 842,
  "filters": {
    "language": "TypeScript",
    "license_policy": "permissive_only"
  }
}
```

### 12.11 FeedbackRecord

```json
{
  "id": "fb_01h...",
  "context_pack_id": "ctx_01h...",
  "task_id": "task_01h...",
  "user_rating": 5,
  "accepted": true,
  "tests_passed": true,
  "lint_passed": true,
  "build_passed": true,
  "merged": false,
  "rollback": false,
  "notes": "Useful guidance; tests were relevant.",
  "created_at": "2026-01-01T00:00:00Z"
}
```

### 12.12 StagedKnowledge

```json
{
  "id": "stage_01h...",
  "source_feedback_id": "fb_01h...",
  "candidate_type": "ImplementationPattern",
  "payload": {},
  "score": 0.78,
  "dedupe_key": "sha256:...",
  "status": "pending",
  "promotion_reason": null,
  "created_at": "2026-01-01T00:00:00Z"
}
```

## 13. SQLite Storage Schema

The exact schema may evolve through migrations, but the MVP should start with these tables.

```sql
CREATE TABLE repositories (
  id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  owner TEXT,
  name TEXT NOT NULL,
  url TEXT,
  default_branch TEXT,
  visibility TEXT NOT NULL,
  license TEXT,
  primary_language TEXT,
  detected_languages_json TEXT NOT NULL DEFAULT '{}',
  detected_frameworks_json TEXT NOT NULL DEFAULT '[]',
  stars INTEGER,
  quality_score REAL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE repository_snapshots (
  id TEXT PRIMARY KEY,
  repo_id TEXT NOT NULL REFERENCES repositories(id),
  commit_sha TEXT,
  branch TEXT,
  indexed_at TEXT NOT NULL,
  file_count INTEGER NOT NULL DEFAULT 0,
  line_count INTEGER NOT NULL DEFAULT 0,
  content_hash TEXT,
  status TEXT NOT NULL
);

CREATE TABLE source_files (
  id TEXT PRIMARY KEY,
  snapshot_id TEXT NOT NULL REFERENCES repository_snapshots(id),
  path TEXT NOT NULL,
  language TEXT,
  mime_type TEXT,
  size_bytes INTEGER NOT NULL,
  line_count INTEGER NOT NULL,
  hash TEXT NOT NULL,
  is_test INTEGER NOT NULL DEFAULT 0,
  is_generated INTEGER NOT NULL DEFAULT 0,
  is_dependency INTEGER NOT NULL DEFAULT 0,
  UNIQUE(snapshot_id, path)
);

CREATE TABLE symbols (
  id TEXT PRIMARY KEY,
  file_id TEXT NOT NULL REFERENCES source_files(id),
  snapshot_id TEXT NOT NULL REFERENCES repository_snapshots(id),
  name TEXT NOT NULL,
  kind TEXT NOT NULL,
  qualified_name TEXT NOT NULL,
  start_line INTEGER,
  end_line INTEGER,
  signature TEXT,
  docstring TEXT,
  visibility TEXT
);

CREATE TABLE dependencies (
  id TEXT PRIMARY KEY,
  snapshot_id TEXT NOT NULL REFERENCES repository_snapshots(id),
  manager TEXT NOT NULL,
  name TEXT NOT NULL,
  version_spec TEXT,
  scope TEXT,
  manifest_path TEXT
);

CREATE TABLE source_refs (
  id TEXT PRIMARY KEY,
  repo_id TEXT NOT NULL REFERENCES repositories(id),
  snapshot_id TEXT NOT NULL REFERENCES repository_snapshots(id),
  file_id TEXT REFERENCES source_files(id),
  path TEXT NOT NULL,
  start_line INTEGER,
  end_line INTEGER,
  license TEXT,
  snippet_allowed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE knowledge_objects (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  problem TEXT,
  solution TEXT,
  when_to_use_json TEXT NOT NULL DEFAULT '[]',
  when_not_to_use_json TEXT NOT NULL DEFAULT '[]',
  language TEXT,
  frameworks_json TEXT NOT NULL DEFAULT '[]',
  domain TEXT,
  tags_json TEXT NOT NULL DEFAULT '[]',
  quality_score REAL NOT NULL DEFAULT 0,
  confidence REAL NOT NULL DEFAULT 0,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE knowledge_object_refs (
  knowledge_object_id TEXT NOT NULL REFERENCES knowledge_objects(id),
  source_ref_id TEXT NOT NULL REFERENCES source_refs(id),
  PRIMARY KEY (knowledge_object_id, source_ref_id)
);

CREATE TABLE graph_nodes (
  id TEXT PRIMARY KEY,
  node_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  label TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE graph_edges (
  id TEXT PRIMARY KEY,
  source_node_id TEXT NOT NULL REFERENCES graph_nodes(id),
  target_node_id TEXT NOT NULL REFERENCES graph_nodes(id),
  edge_type TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 1.0,
  confidence REAL NOT NULL DEFAULT 1.0,
  source TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE TABLE embeddings (
  id TEXT PRIMARY KEY,
  object_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  model TEXT NOT NULL,
  dimension INTEGER NOT NULL,
  vector_uri TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE retrieval_traces (
  id TEXT PRIMARY KEY,
  task TEXT NOT NULL,
  created_at TEXT NOT NULL,
  retrievers_used_json TEXT NOT NULL DEFAULT '[]',
  candidate_count INTEGER NOT NULL,
  reranked_count INTEGER NOT NULL,
  returned_count INTEGER NOT NULL,
  latency_ms INTEGER NOT NULL,
  filters_json TEXT NOT NULL DEFAULT '{}',
  payload_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE context_packs (
  id TEXT PRIMARY KEY,
  retrieval_trace_id TEXT REFERENCES retrieval_traces(id),
  task TEXT NOT NULL,
  task_type TEXT,
  constraints_json TEXT NOT NULL DEFAULT '{}',
  json_payload TEXT NOT NULL,
  markdown_payload TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE feedback_records (
  id TEXT PRIMARY KEY,
  context_pack_id TEXT REFERENCES context_packs(id),
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
  source_feedback_id TEXT REFERENCES feedback_records(id),
  candidate_type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  score REAL NOT NULL DEFAULT 0,
  dedupe_key TEXT,
  status TEXT NOT NULL,
  promotion_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

### 13.1 FTS Tables

```sql
CREATE VIRTUAL TABLE knowledge_fts USING fts5(
  title,
  summary,
  problem,
  solution,
  tags,
  content='knowledge_objects',
  content_rowid='rowid'
);

CREATE VIRTUAL TABLE file_fts USING fts5(
  path,
  content,
  language,
  repo,
  tokenize='porter'
);
```

If rowid mapping is awkward with text IDs, use external content triggers with an integer surrogate key or a separate FTS table storing object_id.

## 14. Knowledge Graph Schema

### 14.1 Node Types

Core graph node types:

- Repository.
- RepositorySnapshot.
- SourceFile.
- Module.
- Symbol.
- Function.
- Class.
- Method.
- Interface.
- Route.
- APIEndpoint.
- TestCase.
- Dependency.
- Framework.
- ProjectProfile.
- ArchitecturePattern.
- ImplementationPattern.
- ModulePattern.
- TestingPattern.
- SecurityPattern.
- AntiPattern.
- DecisionRecord.
- CodeExample.
- Constraint.
- Tradeoff.
- ContextPack.
- FeedbackRecord.

### 14.2 Edge Types

Core edge types:

- CONTAINS: repository contains file, file contains symbol.
- IMPORTS: file imports file or dependency.
- EXPORTS: file exports symbol.
- CALLS: function calls function.
- DEPENDS_ON: module/package depends on dependency.
- TESTED_BY: implementation file or symbol is tested by test.
- DEFINES_ROUTE: file defines route.
- HANDLES_ENDPOINT: function handles API endpoint.
- USES_FRAMEWORK: repo or pattern uses framework.
- IMPLEMENTS: source object implements pattern.
- USES_PATTERN: project or module uses pattern.
- DERIVED_FROM: knowledge object derived from source ref.
- SIMILAR_TO: pattern similar to pattern.
- CONFLICTS_WITH: pattern conflicts with anti-pattern.
- REPLACES: pattern replaces older pattern.
- APPLIES_TO_LANGUAGE: pattern applies to language.
- APPLIES_TO_FRAMEWORK: pattern applies to framework.
- HAS_CONSTRAINT: pattern has constraint.
- HAS_TRADEOFF: pattern has tradeoff.
- PRODUCED_CONTEXT: retrieval trace produced context pack.
- USED_IN_TASK: context pack used in feedback task.
- PROMOTED_FROM: promoted knowledge object promoted from staged object.

### 14.3 Edge Metadata

Every graph edge should support:

```json
{
  "weight": 0.92,
  "confidence": 0.84,
  "source": "deterministic_parser",
  "evidence": ["ref_01h..."],
  "created_at": "2026-01-01T00:00:00Z"
}
```

### 14.4 Graph Usage Rules

Use the graph to:

- Expand from a pattern to examples.
- Expand from a file to tests.
- Expand from a repo to frameworks and conventions.
- Explain why a result was retrieved.
- Discover related implementation patterns.
- Link accepted feedback to promoted knowledge.

Do not use the graph to:

- Store every arbitrary text chunk relationship.
- Replace lexical search.
- Replace vector search.
- Store unbounded noisy similarity edges.

Similarity edges should only be persisted after deduplication and quality thresholds.

## 15. Pattern Extraction Pipeline

### 15.1 Pipeline Overview

```text
Repository Snapshot
  -> File Discovery
  -> Metadata Detection
  -> Deterministic Parsing
  -> Artifact Graph Creation
  -> Candidate Pattern Discovery
  -> Knowledge Object Generation
  -> Validation
  -> Citation Attachment
  -> Scoring
  -> Deduplication
  -> Storage + Indexing
```

### 15.2 Candidate Pattern Discovery

The compiler should find candidates from:

- Repeated module structures.
- Framework-specific route conventions.
- Common dependency combinations.
- Tests that reveal expected behavior.
- Docs that describe architecture decisions.
- Exported APIs.
- Security-sensitive code paths.
- Config conventions.
- Error handling and validation patterns.

### 15.3 Knowledge Object Generation

Generation should produce structured fields:

- title.
- summary.
- problem.
- solution.
- when_to_use.
- when_not_to_use.
- implementation_steps.
- tests_to_consider.
- risks.
- constraints.
- tradeoffs.
- source_refs.
- language.
- frameworks.
- tags.
- confidence.

LLM-assisted generation must use a constrained schema. Invalid JSON must be rejected or repaired through a controlled validation loop.

### 15.4 Scoring

Quality score should consider:

- Repository quality.
- Source file clarity.
- Test coverage evidence.
- Documentation support.
- Citation specificity.
- Pattern reusability.
- Framework relevance.
- Human feedback when available.

Initial scoring formula:

```text
quality_score =
  0.20 * repo_quality +
  0.20 * citation_quality +
  0.20 * test_evidence +
  0.15 * docs_evidence +
  0.15 * pattern_reusability +
  0.10 * extraction_confidence
```

### 15.5 Deduplication

Deduplication should use:

- normalized title.
- tags.
- language/framework.
- source dependency overlap.
- embedding similarity.
- graph neighborhood similarity.

Duplicate candidates should either merge source references into an existing object or create a SIMILAR_TO edge if they are related but not the same.

### 15.6 Citation Policy

Every generated object must have at least one source_ref. Production-quality objects should prefer line-specific citations.

If exact line ranges are unavailable, file-level citations are allowed with lower citation_quality.

## 16. Retrieval Architecture

### 16.1 Retrieval Pipeline

```text
Task Request
  -> Task Classification
  -> Constraint Extraction
  -> Query Planning
  -> Lexical Retrieval
  -> Vector Retrieval
  -> Metadata Filtering
  -> Graph Expansion
  -> Reranking
  -> Context Compression
  -> Context Pack Output
  -> Retrieval Trace Storage
```

### 16.2 Task Classification

Initial task types:

- backend_feature.
- frontend_feature.
- bug_fix.
- refactor.
- test_generation.
- api_integration.
- database_change.
- security_change.
- documentation_change.
- architecture_review.

Classifier can be rule-based first, then LLM-assisted later.

### 16.3 Constraint Extraction

Extract:

- language.
- framework.
- domain.
- repo scope.
- file paths.
- feature type.
- quality threshold.
- license policy.
- max token budget.

### 16.4 Lexical Retrieval

Use SQLite FTS5 for:

- exact framework names.
- package names.
- file paths.
- symbol names.
- domain terms.
- feature names.

### 16.5 Vector Retrieval

Use local vector search for:

- fuzzy task similarity.
- concept matching.
- semantically similar patterns.
- examples whose wording differs from task wording.

MVP options:

- LanceDB.
- sqlite-vec.
- Chroma local.

Recommended MVP default: LanceDB or sqlite-vec depending on installation friction. Keep a VectorStore interface so it can be changed.

### 16.6 Graph Expansion

After initial candidate retrieval, expand:

- Pattern -> CodeExample.
- Pattern -> TestingPattern.
- Pattern -> AntiPattern.
- SourceFile -> TestCase.
- Repository -> ProjectProfile.
- Framework -> applicable patterns.
- Dependency -> common integration patterns.

Expansion must be bounded:

- max_depth default: 2.
- max_neighbors_per_node default: 12.
- min_edge_confidence default: 0.5.

### 16.7 Reranking

Initial reranking formula:

```text
score =
  0.30 * lexical_score +
  0.25 * vector_score +
  0.15 * graph_score +
  0.15 * quality_score +
  0.10 * metadata_match +
  0.05 * recency_score
```

Reranker should be replaceable with a local or external model later.

### 16.8 Context Compression

Compression rules:

- Prefer patterns over raw snippets.
- Prefer line-specific citations.
- Include only short snippets when allowed.
- Remove duplicate advice.
- Group by implementation relevance.
- Include risk and test guidance.
- Respect max_tokens.

### 16.9 Context Pack Schema

```json
{
  "task_type": "backend_feature",
  "summary": "Use token-backed reset flow with server-side validation.",
  "recommended_patterns": [
    {
      "title": "Password reset with server actions",
      "why_relevant": "Matches Next.js App Router and Prisma constraints.",
      "implementation_steps": [],
      "citations": []
    }
  ],
  "relevant_examples": [],
  "architecture_rules": [],
  "tests_to_consider": [],
  "risks": [],
  "avoid": [],
  "source_citations": [],
  "retrieval_trace": {
    "id": "trace_01h...",
    "retrievers_used": ["fts", "vector", "graph"]
  }
}
```

## 17. Reflexion and Learning Architecture

### 17.1 Purpose

Reflexion improves the knowledge base using real task outcomes. The system should learn from accepted implementations, test results, reviewer feedback, and later project signals.

### 17.2 Feedback Signals

Supported signals:

- user accepted implementation.
- user rating.
- tests passed.
- lint passed.
- build passed.
- code was merged.
- reviewer approved.
- rollback did not occur.
- production incident did not occur.
- user marked context useful.

### 17.3 Feedback Pipeline

```text
Context Pack Used
  -> Feedback Record Created
  -> Outcome Signals Attached
  -> Final Implementation Analyzed
  -> Candidate Knowledge Extracted
  -> Deduplication
  -> Quality Scoring
  -> Staged Storage
  -> Human or Policy Review
  -> Promotion to Main Knowledge Store
```

### 17.4 Promotion Policy

Automatic promotion may be allowed only when:

- accepted = true.
- tests_passed = true or not applicable.
- lint_passed = true or not applicable.
- build_passed = true or not applicable.
- score >= configured threshold.
- duplicate check passes.
- citations are present.
- license/privacy policy allows storage.

Default MVP behavior: keep staged knowledge pending and provide CLI command for human review.

### 17.5 Reflexion CLI

Commands:

```bash
repo-wiki feedback submit --context-pack ctx_123 --accepted --tests-passed --rating 5
repo-wiki feedback list --status pending
repo-wiki feedback promote stage_123
repo-wiki feedback reject stage_123 --reason "duplicate"
```

## 18. Storage Architecture

### 18.1 MVP Storage

Use:

- SQLite for metadata, artifacts, graph tables, feedback, traces.
- SQLite FTS5 for lexical search.
- Local vector index for embeddings.
- Markdown/JSON export vault for human-readable knowledge.

### 18.2 Vault Export

Vault export should create:

```text
vault/
  repositories/
    owner__repo/
      project-profile.md
      architecture.md
      patterns/
      tests.md
      dependencies.md
  patterns/
    implementation/
    testing/
    security/
    anti-patterns/
  indexes/
    frameworks.md
    languages.md
    domains.md
```

Vault files are not the primary database. They are a readable export and portfolio artifact.

### 18.3 Migration Strategy

Use Alembic or a lightweight migration runner. Every schema change must have:

- migration file.
- short migration description.
- tests or smoke validation.
- ADR when the change is architectural.

### 18.4 Backup Strategy

For local-first:

- SQLite database file.
- vector index directory.
- vault export directory.
- config file.

Provide:

```bash
repo-wiki backup create ./backups/demo.db.tar.gz
repo-wiki backup restore ./backups/demo.db.tar.gz
```

Backups are optional for MVP but should be considered in the roadmap.

## 19. API Contracts

### 19.1 HTTP API Overview

Base URL:

```text
http://localhost:8000
```

### 19.2 Health

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "database": "ok"
}
```

### 19.3 Ingest Repository

```http
POST /v1/ingest/repository
Content-Type: application/json
```

Request:

```json
{
  "url": "https://github.com/example/project",
  "branch": "main",
  "include": ["**/*.ts", "**/*.tsx", "**/*.md"],
  "exclude": ["node_modules/**", "dist/**"],
  "license_policy": "permissive_only"
}
```

Response:

```json
{
  "job_id": "job_01h...",
  "repo_id": "repo_01h...",
  "snapshot_id": "snap_01h...",
  "status": "queued"
}
```

### 19.4 Ingest Local Repository

```http
POST /v1/ingest/local
```

Request:

```json
{
  "path": "/home/user/project",
  "license_policy": "private_local_only"
}
```

### 19.5 Get Repository

```http
GET /v1/repositories/{repo_id}
```

### 19.6 List Knowledge Objects

```http
GET /v1/knowledge?type=ImplementationPattern&language=TypeScript&framework=Next.js
```

### 19.7 Retrieve Context

```http
POST /v1/retrieve
Content-Type: application/json
```

Request:

```json
{
  "task": "Implement password reset in a Next.js app with Prisma.",
  "language": "TypeScript",
  "framework": "Next.js",
  "domain": "auth",
  "max_tokens": 4000,
  "license_policy": "permissive_only",
  "output_format": "json"
}
```

Response:

```json
{
  "context_pack": {},
  "markdown": "...",
  "trace_id": "trace_01h..."
}
```

### 19.8 Submit Feedback

```http
POST /v1/feedback
```

Request:

```json
{
  "context_pack_id": "ctx_01h...",
  "accepted": true,
  "rating": 5,
  "tests_passed": true,
  "lint_passed": true,
  "build_passed": true,
  "notes": "The generated tests matched the project conventions."
}
```

### 19.9 Metrics

```http
GET /v1/metrics
```

Response:

```json
{
  "indexed_repositories": 128,
  "knowledge_objects": 25400,
  "extracted_patterns": 3500,
  "graph_nodes": 64000,
  "graph_edges": 181000,
  "supported_languages": ["Python", "TypeScript"],
  "supported_interfaces": ["CLI", "HTTP API", "MCP"]
}
```

## 20. CLI Commands

Command name recommendation: `repo-wiki`.

### 20.1 Project Initialization

```bash
repo-wiki init
repo-wiki config show
repo-wiki config set storage.path ./data/repo-wiki.db
```

### 20.2 Ingestion

```bash
repo-wiki ingest github https://github.com/example/project
repo-wiki ingest github https://github.com/example/project --branch main --license-policy permissive_only
repo-wiki ingest local ./my-project --license-policy private_local_only
repo-wiki ingest status job_123
```

### 20.3 Extraction and Compilation

```bash
repo-wiki extract repo_123
repo-wiki compile repo_123
repo-wiki compile repo_123 --llm-provider openai
repo-wiki compile repo_123 --no-llm
```

### 20.4 Retrieval

```bash
repo-wiki retrieve "implement password reset in Next.js with Prisma"
repo-wiki retrieve "add FastAPI endpoint with tests" --language Python --framework FastAPI
repo-wiki retrieve "refactor service layer" --repo repo_123 --max-tokens 3000 --format markdown
```

### 20.5 Knowledge Inspection

```bash
repo-wiki knowledge list --type ImplementationPattern
repo-wiki knowledge show ko_123
repo-wiki graph neighbors ko_123 --edge-type DERIVED_FROM
repo-wiki graph export --format graphml --output docs/diagrams/knowledge.graphml
```

### 20.6 Feedback and Reflexion

```bash
repo-wiki feedback submit --context-pack ctx_123 --accepted --tests-passed --rating 5
repo-wiki feedback list --status pending
repo-wiki feedback promote stage_123
repo-wiki feedback reject stage_123 --reason duplicate
```

### 20.7 Benchmarks

```bash
repo-wiki benchmark run --suite mvp
repo-wiki benchmark report --output docs/benchmarks/mvp-results.md
repo-wiki metrics
```

### 20.8 Services

```bash
repo-wiki api serve --host 127.0.0.1 --port 8000
repo-wiki mcp serve
```

## 21. MCP Server Design

### 21.1 Role

The MCP server allows MCP-compatible coding agents and IDE tools to retrieve repository knowledge using the same core services as the CLI and HTTP API.

MCP is part of Version 1 because it demonstrates modern agent ecosystem support and makes the project portfolio stronger.

### 21.2 MCP Tools

Expose these tools:

#### retrieve_context

Input:

```json
{
  "task": "implement password reset in Next.js with Prisma",
  "language": "TypeScript",
  "framework": "Next.js",
  "repo": "optional repo id",
  "max_tokens": 4000
}
```

Output:

```json
{
  "context_pack": {},
  "markdown": "...",
  "citations": []
}
```

#### search_knowledge

Input:

```json
{
  "query": "FastAPI dependency injection tests",
  "type": "TestingPattern",
  "limit": 10
}
```

#### inspect_repository

Input:

```json
{
  "repo_id": "repo_123"
}
```

#### submit_feedback

Input:

```json
{
  "context_pack_id": "ctx_123",
  "accepted": true,
  "rating": 5,
  "tests_passed": true
}
```

### 21.3 MCP Resources

Expose resources:

- `repo-wiki://repositories`
- `repo-wiki://repositories/{repo_id}`
- `repo-wiki://knowledge/{knowledge_object_id}`
- `repo-wiki://context-packs/{context_pack_id}`
- `repo-wiki://metrics`

### 21.4 MCP Implementation Guidance

Use the official MCP SDK. Keep the server adapter thin:

- parse MCP input.
- call core service.
- return structured output.
- handle validation errors.

Do not duplicate retrieval or storage logic in the MCP layer.

## 22. Service Boundaries

### 22.1 Python Package Boundaries

Recommended package name: `repo_wiki`.

```text
repo_wiki/
  core/
  ingest/
  extract/
  compile/
  storage/
  retrieval/
  graph/
  reflexion/
  interfaces/
  benchmarks/
```

### 22.2 Boundary Rules

- `interfaces/*` may depend on core services.
- `core/*` must not depend on interface adapters.
- `storage/*` owns database access.
- `extract/*` owns language-specific parsing.
- `retrieval/*` owns ranking and context pack generation.
- `graph/*` owns graph table operations and graph algorithms.
- `compile/*` owns pattern generation and validation.
- `reflexion/*` owns feedback and staged learning.

### 22.3 Dependency Direction

```text
interfaces -> core -> domain models
core -> storage ports
core -> extractor ports
storage -> database implementations
extract -> parser implementations
```

Avoid circular imports.

## 23. Directory Structure

Recommended repository structure:

```text
repo-knowledge-compiler/
  README.md
  AGENT.md
  ARCHITECTURE.md
  ROADMAP.md
  DECISIONS.md
  CONTRIBUTING.md
  LICENSE
  pyproject.toml
  uv.lock
  .gitignore
  .env.example
  repo_wiki/
    __init__.py
    config.py
    logging.py
    domain/
      models.py
      enums.py
      errors.py
      ids.py
    core/
      ingestion_service.py
      extraction_service.py
      compiler_service.py
      retrieval_service.py
      context_pack_service.py
      reflexion_service.py
      metrics_service.py
    ingest/
      github.py
      local.py
      filters.py
      license_detector.py
    extract/
      base.py
      file_tree.py
      markdown.py
      python_ast.py
      typescript.py
      package_manifests.py
      tests.py
      routes.py
    compile/
      schemas.py
      generator.py
      scoring.py
      dedupe.py
      prompts/
        implementation_pattern.md
        architecture_pattern.md
        testing_pattern.md
    storage/
      sqlite.py
      migrations/
      fts.py
      vector.py
      repositories.py
    graph/
      service.py
      schema.py
      export.py
    retrieval/
      classifier.py
      planner.py
      lexical.py
      semantic.py
      graph_expand.py
      rerank.py
      context.py
    reflexion/
      feedback.py
      staging.py
      promotion.py
    interfaces/
      cli.py
      api.py
      mcp.py
    benchmarks/
      suites.py
      fixtures.py
      report.py
  tests/
    unit/
    integration/
    fixtures/
  docs/
    architecture/
      software-architecture-specification.md
      system-overview.md
      retrieval.md
      mcp.md
    adr/
      0001-local-first-storage.md
      0002-graph-enhanced-retrieval.md
      0003-mcp-in-version-1.md
    diagrams/
      system-architecture.mmd
      retrieval-pipeline.mmd
      knowledge-graph.mmd
    benchmarks/
      methodology.md
      mvp-results.md
    examples/
      cli.md
      api.md
      mcp.md
    development/
      setup.md
      commits.md
      testing.md
    api/
      http.md
      mcp-tools.md
```

## 24. Tech Stack Decisions and Rationale

### 24.1 Language

Python is the primary implementation language.

Rationale:

- Strong parsing ecosystem.
- FastAPI and Typer are mature.
- SQLite support is built in.
- Good LLM and embedding integration.
- Easy local-first distribution.

### 24.2 CLI

Use Typer.

Rationale:

- Type-hint driven.
- Good help output.
- Simple for portfolio demos.
- Works well with Python services.

### 24.3 HTTP API

Use FastAPI.

Rationale:

- Pydantic integration.
- OpenAPI docs.
- Strong async support.
- Easy local serving.

### 24.4 Data Validation

Use Pydantic.

Rationale:

- Structured models.
- JSON schema generation.
- Validation for LLM output.
- Shared contracts for API and MCP.

### 24.5 Storage

Use SQLite and FTS5 first.

Rationale:

- Local-first.
- Simple deployment.
- Good enough for MVP and demos.
- Supports metadata, graph tables, retrieval logs, and FTS.

### 24.6 Vector Store

Use a replaceable VectorStore interface.

Recommended MVP choices:

- sqlite-vec if simple local embedding search is enough.
- LanceDB if richer local vector indexing is needed.

Decision can be finalized during implementation based on dependency friction.

### 24.7 Graph

Use SQLite graph tables and optional NetworkX.

Rationale:

- Avoid premature Neo4j complexity.
- Preserve graph semantics.
- Easy to export diagrams.
- Good path to Neo4j later if traversal becomes central.

### 24.8 Parsing

Use:

- Python ast for Python.
- tree-sitter for general parsing.
- ts-morph or TypeScript compiler API if TypeScript extraction becomes too limited in Python.

If TypeScript compiler API requires a Node helper, isolate it behind an extractor adapter.

### 24.9 LLM Integration

Use provider interfaces.

Providers:

- no-llm deterministic mode.
- external API provider.
- local model provider.

No core code should depend on a specific vendor.

### 24.10 Testing

Use pytest.

Use:

- unit tests for models, parsers, scoring, retrieval.
- integration tests for SQLite and API.
- golden-file tests for context packs.
- benchmark tests for retrieval quality.

## 25. Development Phases

### Phase 0: Architecture and Repository Foundation

Goal: create a professional, agent-friendly project foundation.

Deliverables:

- SAS.
- README.
- AGENT.md.
- ARCHITECTURE.md.
- ROADMAP.md.
- DECISIONS.md.
- CONTRIBUTING.md.
- docs structure.
- initial ADRs.
- project skeleton.
- pyproject.
- test framework.
- CI config.

Acceptance criteria:

- A coding agent can understand the project from AGENT.md and ARCHITECTURE.md.
- Documentation directories exist.
- At least three ADRs exist.
- README includes vision, quickstart placeholder, architecture, and metrics section.
- `pytest` runs.
- `repo-wiki --help` works once CLI skeleton exists.

### Phase 1: Core Engine

Goal: implement domain models, storage, ingestion, deterministic extraction, graph basics, and compilation skeleton.

Deliverables:

- Pydantic domain models.
- SQLite migrations.
- repository ingestion from local path.
- GitHub ingestion by clone.
- file tree extraction.
- Python extraction.
- TypeScript/JavaScript basic extraction.
- Markdown extraction.
- package manifest extraction.
- graph node/edge storage.
- ProjectProfile generation.
- basic ImplementationPattern generation without LLM.

Acceptance criteria:

- Can index one local repo.
- Can index one public GitHub repo.
- Stores repositories, snapshots, files, symbols, dependencies, source refs.
- Creates graph nodes and edges for CONTAINS, IMPORTS, DEPENDS_ON, DERIVED_FROM.
- Generates at least one ProjectProfile per repo.
- Generates cited knowledge objects.
- Unit and integration tests cover storage and extraction.

### Phase 2: CLI Interface

Goal: expose core workflows through a polished CLI.

Deliverables:

- `repo-wiki init`.
- `repo-wiki ingest github`.
- `repo-wiki ingest local`.
- `repo-wiki retrieve`.
- `repo-wiki knowledge list/show`.
- `repo-wiki graph neighbors/export`.
- `repo-wiki metrics`.
- CLI examples docs.

Acceptance criteria:

- CLI can ingest and retrieve from at least one repo.
- CLI help text is clear.
- CLI returns useful errors.
- Demo commands in docs work.
- Metrics show indexed repositories, files, symbols, knowledge objects, graph nodes, graph edges.

### Phase 3: HTTP API

Goal: expose service contracts for programmatic use.

Deliverables:

- FastAPI app.
- health endpoint.
- ingest endpoints.
- retrieve endpoint.
- knowledge list endpoint.
- feedback endpoint.
- metrics endpoint.
- OpenAPI docs.
- API examples docs.

Acceptance criteria:

- API starts locally.
- `/health` returns ok.
- `/v1/retrieve` returns a valid context pack.
- API schemas match Pydantic models.
- Integration tests cover key endpoints.

### Phase 4: MCP Server

Goal: support modern agent ecosystem integration.

Deliverables:

- MCP server adapter.
- retrieve_context tool.
- search_knowledge tool.
- inspect_repository tool.
- submit_feedback tool.
- MCP resources.
- MCP examples docs.

Acceptance criteria:

- MCP server starts locally.
- MCP tools call core services.
- retrieve_context returns the same context pack shape as CLI/API.
- MCP docs include example config and usage.
- No retrieval logic is duplicated in MCP adapter.

### Phase 5: Hybrid Retrieval and Context Packs

Goal: improve retrieval quality and context pack usefulness.

Deliverables:

- FTS retrieval.
- vector retrieval.
- graph expansion.
- reranking.
- token-budgeted context pack generation.
- retrieval traces.
- golden-file tests.

Acceptance criteria:

- Context packs include patterns, examples, architecture rules, tests, risks, and citations.
- Retrieval trace records candidate counts and latency.
- Reranking uses lexical, vector, graph, quality, metadata, and recency signals.
- Benchmark suite measures retrieval quality.

### Phase 6: Reflexion and Staged Learning

Goal: allow the system to improve from real agent outcomes.

Deliverables:

- feedback records.
- staged knowledge table.
- feedback CLI.
- feedback API.
- staged promotion/rejection.
- scoring and dedupe for staged knowledge.

Acceptance criteria:

- User can submit feedback for a context pack.
- Feedback can generate staged candidate knowledge.
- Staged knowledge is not automatically promoted by default.
- Promotion preserves provenance.

### Phase 7: Portfolio Hardening and Scale Demo

Goal: make the project convincing to reviewers and recruiters.

Deliverables:

- Professional README.
- architecture diagrams.
- benchmark results.
- demo GIFs or terminal recordings.
- 100+ repo indexing benchmark.
- public roadmap.
- clean ADR list.
- CI status.

Acceptance criteria:

- README shows metrics such as indexed repositories, extracted patterns, knowledge nodes, supported languages, and supported interfaces.
- Benchmark report is reproducible.
- Demo can be run by following docs.
- Commit history is conventional and readable.

## 26. MVP Scope

The MVP must include:

- Local-first project setup.
- Python implementation.
- SQLite metadata and graph storage.
- SQLite FTS5 lexical retrieval.
- Optional local vector index behind interface.
- Public GitHub ingestion.
- Local repo ingestion.
- Python and TypeScript/JavaScript basic extraction.
- Markdown and dependency manifest extraction.
- ProjectProfile and ImplementationPattern generation.
- Context pack retrieval.
- CLI.
- HTTP API.
- MCP server.
- Feedback submission and staged knowledge records.
- Docs structure.
- ADRs.
- Benchmarks methodology.

MVP should not include:

- Neo4j.
- cloud deployment.
- hosted SaaS.
- user accounts.
- browser UI.
- full distributed worker system.

## 27. Future Scalability Considerations

### 27.1 Path to 100,000 Repositories

The design should evolve as follows:

MVP:

- SQLite.
- local vector index.
- single process ingestion.
- graph tables.

Scale stage 1:

- PostgreSQL for metadata.
- Qdrant for vector search.
- object storage for raw extracted artifacts.
- background workers.
- queue-based ingestion.

Scale stage 2:

- distributed extraction workers.
- partitioned metadata.
- incremental indexing service.
- retrieval cache.
- separate reranking service.

Scale stage 3:

- graph database if traversal complexity justifies it.
- multi-tenant security.
- hosted API.
- web dashboard.

### 27.2 Migration Targets

- SQLite -> PostgreSQL.
- SQLite FTS5 -> PostgreSQL full-text or OpenSearch.
- local vector -> Qdrant.
- SQLite graph tables -> Neo4j only if required.
- local files -> object storage.
- in-process jobs -> Temporal/Prefect/Celery.

### 27.3 Scaling Risks

- license compliance at large scale.
- duplicate pattern explosion.
- low-quality repository pollution.
- vector index drift.
- expensive LLM-based extraction.
- noisy graph edges.
- stale snapshots.
- retrieval latency.

Mitigations:

- strict metadata filters.
- quality scoring.
- staged promotion.
- batch deduplication.
- incremental indexing.
- bounded graph expansion.
- benchmark-driven tuning.

## 28. Implementation Priorities

Priority order:

1. Domain models and schemas.
2. SQLite migrations.
3. Ingestion.
4. Deterministic extraction.
5. Source references and citations.
6. Knowledge object generation.
7. FTS indexing.
8. Graph nodes and edges.
9. Retrieval planner.
10. Context pack generation.
11. CLI.
12. HTTP API.
13. MCP server.
14. Reflexion staging.
15. Benchmarks and portfolio docs.

Do not implement advanced LLM extraction before deterministic extraction is working.

Do not implement Neo4j before graph table retrieval shows a real bottleneck.

Do not implement a UI before CLI/API/MCP are useful.

## 29. Coding Guidelines

### 29.1 General

- Keep core logic independent from CLI/API/MCP.
- Use typed Pydantic models for public contracts.
- Use dataclasses or Pydantic models consistently.
- Keep functions small and testable.
- Prefer explicit errors over silent failure.
- Preserve source provenance.
- Add comments only for non-obvious logic.
- Avoid global mutable state.

### 29.2 Storage

- Use transactions for multi-table writes.
- Keep SQL in storage layer.
- Add indexes intentionally.
- Validate JSON fields before writing.
- Never store embeddings without content hash and model name.

### 29.3 Extraction

- Treat source files as untrusted text.
- Never execute repository code.
- Skip huge files by default.
- Record extraction failures.
- Keep language extractors behind a common interface.

### 29.4 Retrieval

- Log retrieval traces.
- Keep scoring explainable.
- Respect license policy.
- Respect token budget.
- Include citations.
- Prefer compact guidance over long raw excerpts.

### 29.5 LLM Use

- Put all LLM calls behind provider interfaces.
- Require schema validation.
- Use deterministic fallback.
- Do not send private repo content externally unless configured.
- Store prompt version with generated object metadata.

### 29.6 Documentation

- Update docs with architecture changes.
- Add ADRs for meaningful decisions.
- Keep examples runnable.
- Keep README metrics current.

## 30. Testing Strategy

### 30.1 Unit Tests

Cover:

- ID generation.
- Pydantic validation.
- license policy.
- file filtering.
- Python extraction.
- Markdown extraction.
- dependency parsing.
- scoring.
- deduplication.
- retrieval ranking.
- context pack generation.

### 30.2 Integration Tests

Cover:

- SQLite migrations.
- local repo ingestion.
- GitHub ingestion with fixture or mocked clone.
- FTS retrieval.
- graph expansion.
- CLI commands.
- API endpoints.
- MCP tools.

### 30.3 Golden Tests

Use fixture repositories and expected context packs. These tests protect context pack format and retrieval quality.

### 30.4 Benchmark Tests

Benchmark:

- indexing time.
- retrieval latency.
- citation correctness.
- retrieval precision.
- context usefulness.
- duplicate rate.
- pattern count.

## 31. Benchmark Methodology

### 31.1 MVP Benchmark

Index:

- 10 small repos.
- 10 medium repos.
- at least 5 Python repos.
- at least 5 TypeScript repos.

Measure:

- total files.
- indexed files.
- symbols extracted.
- dependencies extracted.
- knowledge objects created.
- graph nodes.
- graph edges.
- retrieval latency.
- citation correctness sample.

### 31.2 Portfolio Benchmark

Target public metrics:

- Indexed repositories: 100+
- Extracted patterns: 3,500+
- Knowledge nodes: 25,000+
- Supported languages: Python, TypeScript
- Supported interfaces: CLI, HTTP API, MCP

These numbers should be real benchmark outputs, not static claims.

### 31.3 Quality Evaluation

Create a fixed task suite:

- 10 backend tasks.
- 10 frontend tasks.
- 10 testing tasks.
- 10 refactor tasks.
- 10 bug-fix tasks.

For each task:

- retrieve context pack.
- judge top-k relevance.
- check citation validity.
- check whether recommended tests are useful.
- compare agent output with and without context when feasible.

## 32. Documentation Strategy

Documentation is part of the architecture.

Required structure:

```text
docs/
  architecture/
  adr/
  diagrams/
  benchmarks/
  examples/
  development/
  api/
```

Required top-level files:

- README.md.
- AGENT.md.
- ARCHITECTURE.md.
- ROADMAP.md.
- DECISIONS.md.
- CONTRIBUTING.md.

### 32.1 README Requirements

README should include:

- one-paragraph product explanation.
- architecture diagram.
- quickstart.
- supported languages.
- supported interfaces.
- example CLI command.
- example API request.
- example MCP tool.
- benchmark metrics.
- roadmap.
- links to docs.

### 32.2 ADR Requirements

Each ADR should include:

- status.
- context.
- decision.
- consequences.
- alternatives considered.

Initial ADRs:

- Local-first SQLite storage.
- Graph-enhanced retrieval instead of graph-only.
- MCP in Version 1.
- Documentation as first-class deliverable.

### 32.3 Diagrams

Use Mermaid diagrams stored as `.mmd` files.

Required diagrams:

- system architecture.
- ingestion pipeline.
- extraction pipeline.
- retrieval pipeline.
- knowledge graph schema.
- interface architecture.
- Reflexion pipeline.

## 33. Commit Strategy

Use conventional commits.

Good examples:

```text
docs(architecture): add software architecture specification
feat(storage): implement sqlite metadata layer
feat(parser): add python ast extraction pipeline
feat(retrieval): add hybrid lexical retrieval
feat(patterns): implement pattern extraction engine
feat(api): add retrieve context endpoint
feat(mcp): add retrieve_context tool
test(storage): cover repository snapshot persistence
docs(benchmarks): add mvp benchmark methodology
```

Avoid:

```text
fix
update
test
wip
final
new stuff
```

First-phase workflow:

```text
Agent creates commit
  -> Human review
  -> Human pushes
```

Do not let the agent push directly during the first phase.

## 34. Security Considerations

### 34.1 Repository Content

Indexed repositories are untrusted input.

Rules:

- Do not execute repo code.
- Do not run install scripts.
- Do not import repo modules.
- Do not parse with tools that execute code.
- Limit file size.
- Sanitize paths.
- Prevent path traversal.

### 34.2 Secrets

The system should detect obvious secrets and avoid storing or returning them.

Initial secret detection:

- common API key patterns.
- `.env` files excluded by default.
- private key markers.
- GitHub tokens.
- AWS keys.

### 34.3 External LLM Calls

Rules:

- Disabled by default for private repos.
- Configurable for public repos.
- Prompt content should be minimized.
- Record provider and prompt version.
- Never send secrets.

### 34.4 License

Rules:

- Store license metadata.
- Apply snippet policy.
- Prefer summaries and patterns over code copying.
- Return citations for source-derived knowledge.

## 35. Deployment Strategy

### 35.1 Local Development

Use:

```bash
uv sync
repo-wiki init
repo-wiki api serve
repo-wiki mcp serve
```

### 35.2 Docker Compose

Optional later:

```text
docker-compose.yml
  api
  mcp
  qdrant optional
```

### 35.3 CI

CI should run:

- formatting check.
- linting.
- type checking.
- unit tests.
- integration tests.
- docs link check when practical.

Recommended tools:

- ruff.
- mypy or pyright.
- pytest.
- pre-commit.

## 36. Configuration

Use `repo-wiki.toml` or environment variables.

Example:

```toml
[storage]
sqlite_path = ".repo-wiki/repo-wiki.db"
vector_path = ".repo-wiki/vector"
vault_path = ".repo-wiki/vault"

[ingestion]
max_file_size_bytes = 1000000
exclude = ["node_modules/**", ".git/**", "dist/**", "build/**", ".venv/**"]

[license]
policy = "permissive_only"

[llm]
provider = "none"
allow_private_repo_content = false

[retrieval]
max_tokens = 4000
graph_max_depth = 2
graph_max_neighbors = 12
```

## 37. Error Handling

Define domain errors:

- RepositoryNotFound.
- UnsupportedSource.
- LicensePolicyViolation.
- ExtractionFailed.
- KnowledgeValidationFailed.
- RetrievalFailed.
- StorageError.
- MCPValidationError.

Interfaces should convert these to:

- CLI readable messages.
- HTTP status codes.
- MCP tool errors.

## 38. Observability

Log:

- ingestion start/end.
- extraction failures.
- compiler validation failures.
- retrieval trace.
- API requests.
- MCP tool calls.
- feedback events.

Metrics:

- indexed repositories.
- indexed files.
- extracted symbols.
- knowledge objects.
- graph nodes.
- graph edges.
- retrieval latency.
- context pack size.
- citation coverage.
- failed extraction count.

## 39. Acceptance Criteria Summary

Version 1 is acceptable when:

- A user can install and run the project locally.
- A user can index at least one public GitHub repo.
- A user can index at least one local repo.
- The system extracts files, symbols, dependencies, docs, and basic tests.
- The system compiles cited ProjectProfile and ImplementationPattern objects.
- The system stores metadata, FTS index, graph nodes, and graph edges.
- The system retrieves context packs through CLI, HTTP API, and MCP.
- Context packs include citations, risks, and tests to consider.
- Feedback can be submitted and staged.
- Docs include README, AGENT, ARCHITECTURE, ROADMAP, DECISIONS, CONTRIBUTING, ADRs, diagrams, examples, and benchmark methodology.
- Tests cover critical core behavior.
- Benchmark docs show real metrics.

## 40. Initial GitHub Milestones

### Milestone 1: Architecture Foundation

Issues:

- Create project skeleton.
- Add SAS and docs structure.
- Add AGENT.md and top-level docs.
- Add ADR templates and initial ADRs.
- Configure pyproject, ruff, pytest.

### Milestone 2: Storage and Domain Models

Issues:

- Implement Pydantic domain models.
- Add SQLite migrations.
- Implement repository and snapshot persistence.
- Add source refs and knowledge object storage.
- Add graph nodes and edges.

### Milestone 3: Ingestion and Extraction

Issues:

- Implement local ingestion.
- Implement GitHub ingestion.
- Implement file filtering.
- Implement Python extraction.
- Implement TypeScript extraction.
- Implement Markdown and package manifest extraction.

### Milestone 4: Knowledge Compilation

Issues:

- Generate ProjectProfile.
- Generate ImplementationPattern.
- Add scoring.
- Add citations.
- Add deduplication.

### Milestone 5: Retrieval and Context Packs

Issues:

- Add FTS retrieval.
- Add vector store interface.
- Add graph expansion.
- Add reranking.
- Add context pack generator.

### Milestone 6: Interfaces

Issues:

- Implement CLI.
- Implement HTTP API.
- Implement MCP server.
- Add examples for each interface.

### Milestone 7: Reflexion and Benchmarks

Issues:

- Implement feedback records.
- Implement staged knowledge.
- Implement promotion workflow.
- Add benchmark suite.
- Publish benchmark report.

## 41. Implementation Notes for Autonomous Agents

When building from this specification:

1. Start with documentation and skeleton.
2. Implement storage before retrieval.
3. Implement deterministic extraction before LLM generation.
4. Keep interfaces thin.
5. Add tests with each component.
6. Keep commits small and conventional.
7. Update ADRs when decisions change.
8. Never add dependencies without a clear reason.
9. Do not introduce Neo4j, cloud services, or UI unless the roadmap phase requires it.
10. Keep context packs cited and compact.

The project succeeds when it can prove that structured repository knowledge improves coding-agent behavior with measurable, cited, reproducible outputs.
