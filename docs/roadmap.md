# Roadmap

repo-wiki is an experimental local-first repository intelligence project. This roadmap separates what exists in v0.1 from the next research and engineering steps.

## v0.1

- Local-first repository ingestion.
- Public GitHub and local repository support.
- Python / TypeScript / JavaScript support.
- Deterministic source, docs, tests, route, and package extraction.
- SQLite metadata, FTS, graph tables, retrieval traces, context packs, and feedback.
- Hybrid lexical, local vector, graph-expanded retrieval.
- Role-labeled cited context packs.
- CLI interface.
- Lightweight HTTP and MCP-compatible interfaces.
- Benchmark documentation.
- Retrieval v0.1 blind holdout.

## v0.2

- Better context-to-action planning.
- Stronger source-to-test pairing.
- More robust behavioral constraint extraction.
- Better MCP integration.
- Improved coding-agent A/B benchmark.
- Retrieval-only regression checks before coding benchmarks.
- Cleaner benchmark runner that records traces, expected files, and reports in one command.

## v0.3

- Multi-agent comparison.
- opencode / Claude Code / Codex-style workflows.
- Obsidian vault export improvements.
- Larger language support.
- Better graph reasoning.
- More scalable indexing and incremental ingestion.
- More rigorous production security review.

## Open questions

- How much context should be role-labeled versus left as raw cited evidence?
- Which retrieval-only metrics best predict coding-agent patch quality?
- When should repo-wiki prefer exact symbol/path matches over broader runtime context?
- What is the minimum MCP workflow that materially improves agent behavior?
