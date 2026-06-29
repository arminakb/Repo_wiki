# Decisions

This file indexes architecture decisions. Full ADRs live in `docs/adr/`.

## Accepted

- ADR 0001: Local-first SQLite storage.
- ADR 0002: Graph-enhanced retrieval instead of graph-only retrieval.
- ADR 0003: MCP server included in Version 1.
- ADR 0004: Documentation and presentation as first-class deliverables.
- ADR 0005: Thin standard-library interfaces for Version 1.
- ADR 0006: Versioned SQLite and TOML config.

## Pending

- Final local vector store: LanceDB vs sqlite-vec.
- TypeScript extraction strategy: tree-sitter only vs Node helper using TypeScript compiler API.
- External LLM provider interface details.
- Benchmark fixture repository list.

## Decision Rules

Use an ADR when a change affects:

- storage architecture.
- retrieval architecture.
- graph schema.
- public API contracts.
- supported interfaces.
- license/privacy policy.
- major dependencies.
- scaling strategy.

Do not add major dependencies without updating this file or adding an ADR.
