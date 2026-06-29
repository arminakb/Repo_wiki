# Architecture Overview

repo-wiki is a local-first repository intelligence engine for coding-agent workflows. Its job is to turn real repositories into cited, task-specific context packs that help an agent or developer find the right files before editing.

```text
Repository
   ↓
Ingestion
   ↓
Source / docs / tests / configs extraction
   ↓
SQLite + FTS + vector scoring + graph tables
   ↓
Hybrid retrieval
   ↓
Role-labeled cited context pack
   ↓
Coding agent / developer
```

## System purpose

The system indexes repositories, extracts deterministic code facts, stores cited knowledge locally, and retrieves compact context for a specific coding task. It is graph-enhanced rather than graph-only: lexical search, local vector scoring, metadata filtering, graph relationships, and reranking all contribute to the final pack.

## Ingestion pipeline

Ingestion accepts local paths and public GitHub URLs. It records repository metadata, source type, visibility, license policy, detected languages, frameworks, snapshots, file hashes, and extraction metrics.

Generated folders, dependency folders, local repo-wiki state, caches, and configured excludes are skipped before extraction.

## Extraction pipeline

Extraction is deterministic and runs before any retrieval reasoning. It collects:

- source files and line counts,
- Python symbols and imports,
- TypeScript/JavaScript imports, exports, functions, classes, and route-like files,
- Markdown structure,
- package manifests and dependencies,
- tests and likely source/test relationships,
- source references for citations.

## Storage layer

The v0.1 storage backend is SQLite:

- metadata tables for repositories, snapshots, files, symbols, dependencies, and source refs,
- knowledge objects with typed payloads,
- graph nodes and edges,
- SQLite FTS5 for lexical search,
- deterministic local hash-vector scoring behind a replaceable interface,
- retrieval traces, context packs, feedback, staged knowledge, and schema metadata.

## Retrieval pipeline

```text
Task
   ↓
Task classification and entity extraction
   ↓
Lexical + source-file + vector candidates
   ↓
Graph expansion and source/test pairing
   ↓
Explainable reranking
   ↓
Citation filtering and context compression
   ↓
Context pack
```

Retrieval v0.1 prioritizes exact task entities, path/stem matches, related tests, and cited evidence. It also emits warnings when exact task entities are missing or when results look provisional.

## Context-pack generation

A context pack includes:

- recommended patterns,
- relevant examples,
- architecture rules,
- implementation steps,
- tests to consider,
- risks and low-quality warnings,
- source citations,
- short behavioral notes when local guards or early-return branches are detected.

The schema marker is `context_pack.v1`.

## Interfaces

All interfaces call the same core services:

- CLI through `repo_wiki.interfaces.cli`,
- lightweight stdlib HTTP server plus optional FastAPI app factory,
- MCP-compatible JSON-RPC stdio adapter.

## Benchmark and evaluation flow

Benchmark artifacts are documentation-first:

1. choose fixed repositories and tasks,
2. define expected source, test, runtime, or convention files before retrieval results are used,
3. run ingestion and retrieval with a clean data directory,
4. record top results, citations, warnings, latency, and expected-file hits,
5. compare retrieval quality separately from coding-agent implementation quality.

See [docs/benchmarks/README.md](benchmarks/README.md) for current results and limitations.
