# Architecture

repo-wiki is a local-first repository intelligence pipeline for coding-agent context retrieval.

## System Flow

```text
Local path or GitHub URL
  -> ingestion and license metadata
  -> deterministic extraction
  -> SQLite source, symbol, graph, and FTS tables
  -> hybrid retrieval and reranking
  -> cited context_pack.v1
  -> CLI / HTTP / MCP-compatible stdio
```

## Main Components

- `repo_wiki/ingest/`: local and GitHub repository intake.
- `repo_wiki/extract/`: file tree, Python, TypeScript/JavaScript, Markdown, route, and package extraction.
- `repo_wiki/compile/`: source artifacts to typed knowledge objects.
- `repo_wiki/storage/`: SQLite schema, FTS, graph tables, traces, context packs, feedback, and local vector scoring.
- `repo_wiki/core/`: ingestion, retrieval, metrics, extraction, and feedback services.
- `repo_wiki/retrieval/`: task classification, context assembly, quality gates, and reranking.
- `repo_wiki/interfaces/`: CLI, lightweight HTTP API, optional FastAPI app factory, and MCP-compatible stdio adapter.
- `tests/`: end-to-end and retrieval-quality regression tests.

## Retrieval Pipeline

```text
Task
  -> classify task type and constraints
  -> extract path and symbol hints
  -> search source files and knowledge objects
  -> apply repo/language/framework/license filters
  -> add related tests and use-site files
  -> expand bounded graph relationships
  -> rerank with explainable signals
  -> generate context_pack.v1 with citations
```

## Storage

The project uses SQLite for v0.1:

- repository metadata,
- source files and source references,
- extracted symbols and dependencies,
- knowledge objects,
- graph nodes and edges,
- FTS indexes,
- retrieval traces,
- context packs,
- feedback and staged knowledge.

The local vector layer is deterministic and lightweight. It is useful for portfolio-scale experiments, but it is not a substitute for semantic embeddings in larger evaluations.

## Interface Boundary

The CLI, HTTP API, and MCP-compatible adapter call the same core services. Business logic lives in `repo_wiki/core/`, not in the interface adapters.

## Security And Safety

- Indexed repository code is treated as untrusted text.
- repo-wiki does not execute indexed repository code.
- Source references preserve license and snippet-policy metadata.
- Local data is stored under `.repo-wiki/` by default and is ignored by git.

## Technical Interest

repo-wiki combines deterministic static extraction, local-first storage, graph relationships, retrieval traces, role-labeled context packs, and benchmark feedback into one small system that can be inspected and run locally.
