# Architecture

Repo Knowledge Compiler is a local-first knowledge compiler and retrieval engine for coding agents.

The system ingests repositories, extracts deterministic code intelligence, compiles typed knowledge objects, stores useful graph relationships, and returns compact context packs through CLI, HTTP API, and MCP.

For the complete specification, read `SAS.md`.

## System Shape

```text
GitHub / Local Repos
  -> Metadata + License Validation
  -> Deterministic Extraction
  -> Knowledge Compiler
  -> SQLite + FTS5 + Vector Index + Graph Tables
  -> Retrieval Planner
  -> Context Pack Generator
  -> CLI / HTTP API / MCP Server
  -> Reflexion + Staged Learning
```

## Core Principle

The project is graph-enhanced, not graph-only.

The graph is useful for relationships:

- file imports file.
- test tests module.
- repo uses framework.
- pattern applies to framework.
- knowledge object derived from source.
- pattern conflicts with anti-pattern.

Retrieval still needs lexical search, metadata filtering, local vector scoring, graph expansion, reranking, and context compression.

## Components

### Source Intake

Ingests GitHub and local repositories. Records owner, name, URL, branch, commit SHA, license, visibility, languages, frameworks, and snapshot hash.

### Deterministic Extraction

Extracts files, symbols, imports, exports, dependencies, docs, routes, tests, and source references. This layer runs before LLM reasoning.

### Knowledge Compiler

Converts artifacts into typed, cited knowledge objects:

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

### Storage

MVP storage:

- SQLite for metadata and graph tables.
- SQLite FTS5 for lexical search.
- deterministic local hash-vector index behind an interface.
- Markdown/JSON vault export for readable docs.

### Retrieval

Pipeline:

```text
Task
  -> classify
  -> extract constraints
  -> lexical retrieval
  -> hash-vector scoring
  -> metadata/license filtering
  -> graph expansion
  -> reranking
  -> context compression
  -> cited context pack
```

### Reflexion

Captures feedback and objective signals after an agent uses a context pack. New knowledge is staged first, then scored, deduplicated, and promoted into durable knowledge objects only when it passes policy.

### Interfaces

Version 1 includes:

- CLI.
- HTTP API with an optional FastAPI app factory and a dependency-free stdlib server.
- MCP-compatible JSON-RPC stdio adapter.

All three call the same core services.

## Version 1 Acceptance

Version 1 is acceptable when a user can:

- index a local repo.
- index a public GitHub repo.
- extract Python and TypeScript/JavaScript metadata.
- generate cited knowledge objects.
- retrieve a repo-scoped context pack through CLI, HTTP API, and MCP-compatible stdio.
- submit feedback.
- view project metrics and benchmark documentation.
