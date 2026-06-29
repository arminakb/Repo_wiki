# Demo Script

Run this from the repository root.

```bash
python3 -m repo_wiki.interfaces.cli init
python3 -m repo_wiki.interfaces.cli ingest local . --include "repo_wiki/**/*.py" --include "README.md"
python3 -m repo_wiki.interfaces.cli retrieve "add FastAPI auth tests" --language Python --framework FastAPI
python3 -m repo_wiki.interfaces.cli metrics
python3 -m repo_wiki.interfaces.cli benchmark report --output docs/benchmarks/mvp-results.md
```

Expected result:

- ingestion prints extraction metrics and graph counts.
- retrieval prints a cited context pack.
- metrics shows CLI, HTTP API, and MCP as supported interfaces.
- benchmark report contains real local index numbers.
