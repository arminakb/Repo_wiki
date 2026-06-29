# Changelog

## v0.1.0

- Local-first repository ingestion for local paths and public GitHub URLs.
- Deterministic Python and TypeScript/JavaScript extraction, cited knowledge objects, SQLite FTS/vector retrieval, graph expansion, and Reflexion feedback.
- CLI, HTTP API, optional FastAPI app factory, and MCP-compatible stdio adapter.
- Local benchmark reporting with latency, citation coverage, expected-file hits, top-k precision, and per-category quality.

Known limitations:

- The published report is local MVP validation, not the unproven 20-repository or 100+ repository portfolio target.
- TypeScript extraction uses a lightweight standard-library scanner, not the TypeScript compiler.
- The MCP adapter is JSON-RPC stdio compatible and intentionally defers the official SDK wrapper.
