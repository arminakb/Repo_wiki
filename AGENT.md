# AGENT.md

This file is the operating guide for autonomous coding agents working on Repo Knowledge Compiler.

Primary source of truth: `SAS.md`.
Architecture summary: `ARCHITECTURE.md`.
Roadmap: `ROADMAP.md`.
Decision index: `DECISIONS.md`.

## Mission

Build a local-first repository knowledge compiler that helps coding agents write cleaner code by retrieving compact, cited implementation context from indexed repositories.

This project is not a chatbot and not only a graph database. It compiles repositories into structured knowledge objects, stores useful graph relationships, and exposes retrieval through CLI, HTTP API, and MCP server.

## Required Version 1 Interfaces

Version 1 must include:

- CLI.
- HTTP API.
- MCP server.

Implementation order:

1. Core engine.
2. CLI.
3. HTTP API.
4. MCP server.

All interfaces must call the same core services. Do not duplicate business logic in interface adapters.

## Architectural Rules

- Deterministic extraction before LLM reasoning.
- Cited knowledge only.
- Graph-enhanced retrieval, not graph-only retrieval.
- Local-first storage.
- License and privacy metadata are mandatory.
- Feedback goes to staging before durable promotion.
- Documentation is part of the architecture.
- Presentation deliverables are first-class project work.

## Core Components

Implement these services:

- `IngestionService`
- `ExtractionService`
- `KnowledgeCompilerService`
- `GraphService`
- `RetrievalService`
- `ContextPackService`
- `ReflexionService`
- `MetricsService`

## MVP Storage

Use:

- SQLite for metadata, artifacts, graph tables, feedback, and retrieval traces.
- SQLite FTS5 for lexical search.
- Deterministic local hash-vector scoring, replaceable later with real embeddings.
- Markdown/JSON vault export for human-readable output.

Do not add Neo4j in Version 1.

## Initial Language Scope

Support:

- Python.
- TypeScript/JavaScript.
- Markdown documentation.
- Python and Node package manifests.

## Repository Structure

Target structure:

```text
repo_wiki/
  domain/
  core/
  ingest/
  extract/
  compile/
  storage/
  graph/
  retrieval/
  reflexion/
  interfaces/
  benchmarks/
tests/
docs/
  architecture/
  adr/
  diagrams/
  benchmarks/
  examples/
  development/
  api/
```

## Development Priorities

Build in this order:

1. Domain models and schemas.
2. SQLite schema migrations.
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

## Required Context Pack Behavior

Retrieval must return:

- task type.
- recommended patterns.
- relevant examples.
- architecture rules.
- implementation steps.
- tests to consider.
- risks and anti-patterns.
- source citations.
- retrieval trace ID.

Respect license policy and token budget.

## Coding Guidelines

- Keep core logic independent from CLI/API/MCP.
- Use Pydantic models for public contracts.
- Treat indexed repositories as untrusted input.
- Never execute indexed repository code.
- Use transactions for multi-table writes.
- Log extraction failures without crashing full ingestion unless metadata is invalid.
- Keep scoring explainable.
- Add tests with each component.
- Update docs and ADRs when architecture changes.

## Commit Strategy

Use conventional commits:

```text
feat(parser): add python ast extraction pipeline
feat(storage): implement sqlite metadata layer
feat(retrieval): add hybrid lexical retrieval
feat(mcp): add retrieve_context tool
docs(architecture): add retrieval planner design
test(storage): cover repository snapshot persistence
```

Avoid vague commits such as `fix`, `update`, `wip`, `test`, or `final`.

First development phase workflow:

```text
Agent creates commit
Human reviews
Human pushes
```

## Acceptance Gate

Before marking Version 1 complete, verify:

- local repo ingestion works.
- public GitHub ingestion works.
- Python and TypeScript extraction work at a basic level.
- knowledge objects have citations.
- graph nodes and typed edges are stored.
- retrieval works through CLI, HTTP API, and MCP.
- context packs include risks, tests, and citations.
- feedback can be submitted, staged, and promoted into durable knowledge.
- README, architecture docs, ADRs, diagrams, examples, and benchmark docs exist.

## Current Execution Notes

The first implementation is runnable as:

```bash
python3 -m repo_wiki.interfaces.cli init
python3 -m repo_wiki.interfaces.cli ingest local .
python3 -m repo_wiki.interfaces.cli retrieve "implement FastAPI auth tests"
python3 -m unittest discover -s tests -v
```

The HTTP API and MCP adapter are lightweight standard-library implementations for this milestone. The SAS still defines FastAPI and official MCP SDK as the intended mature adapters.
