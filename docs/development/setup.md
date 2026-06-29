# Development Setup

Current local setup:

```bash
python3 -m repo_wiki.interfaces.cli init
python3 -m repo_wiki.interfaces.cli ingest local .
python3 -m repo_wiki.interfaces.cli retrieve "implement FastAPI auth tests"
python3 -m repo_wiki.interfaces.cli repositories list
python3 -m repo_wiki.interfaces.cli backup create /tmp/repo-wiki-backup.sqlite
python3 -m unittest discover -s tests -v
```

Optional package install:

```bash
python3 -m pip install -e .
repo-wiki --help
```

Optional local config:

```toml
[storage]
data_dir = ".repo-wiki"
sqlite_path = ".repo-wiki/repo-wiki.db"

[ingestion]
max_file_size_bytes = 1000000
default_excludes = [".git", ".repo-wiki", "node_modules", "vendor", "dist", "build"]

[license]
policy = "permissive_only"

[retrieval]
max_tokens = 4000

[llm]
provider = "disabled"
```

Environment variables such as `REPO_WIKI_DATA_DIR`, `REPO_WIKI_DB`,
`REPO_WIKI_MAX_FILE_SIZE`, `REPO_WIKI_LICENSE_POLICY`, and
`REPO_WIKI_MAX_TOKENS` override `repo-wiki.toml`.

The architecture allows `uv`, `pytest`, FastAPI, and official MCP SDK usage later, but the first implementation is runnable with the standard library plus Pydantic.
