# Benchmark Methodology

Benchmarks must report real measurements.

## MVP Benchmark

Index:

- 10 small repositories.
- 10 medium repositories.
- at least 5 Python repositories.
- at least 5 TypeScript repositories.

Measure:

- indexed repositories.
- indexed files.
- extracted symbols.
- dependencies.
- knowledge objects.
- graph nodes.
- graph edges.
- retrieval latency.
- citation correctness.
- expected-file hits or top-k precision when a judged task provides expected paths.

## Dataset Policy

`dataset/graphrag-main/` is a bundled GraphRAG snapshot used for local stress validation.
It is excluded from Ruff linting and should not be treated as project source code.
If the snapshot is removed for publication, replace it with instructions to fetch GraphRAG
externally before running GraphRAG-specific benchmark checks.

## Planned Portfolio Target

- Indexed repositories: 100+
- Extracted patterns: 3,500+
- Knowledge nodes: 25,000+
- Supported languages: Python, TypeScript
- Supported interfaces: CLI, HTTP API, MCP

Run a scale benchmark from a newline-delimited URL list:

```bash
python3 -m repo_wiki.interfaces.cli benchmark ingest-list docs/benchmarks/repos.txt
python3 -m repo_wiki.interfaces.cli benchmark report --output docs/benchmarks/mvp-results.md
```

Do not publish target numbers until the report is regenerated from the populated local index.
