# Testing Strategy

Test layers:

- unit tests for models, parsers, scoring, retrieval, and context packs.
- integration tests for SQLite, CLI, API, and MCP.
- golden tests for context pack output.
- benchmarks for retrieval quality and latency.

Critical rule: no indexed repository code should be executed during tests or ingestion.

Release checks:

```bash
python -m compileall repo_wiki
python -m ruff check .
python -m unittest discover -s tests -v
```
