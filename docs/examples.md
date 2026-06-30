# Examples

## CLI

Initialize local storage:

```bash
python3 -m repo_wiki.interfaces.cli init
```

Index a local repository:

```bash
python3 -m repo_wiki.interfaces.cli ingest local .
```

Retrieve a context pack:

```bash
python3 -m repo_wiki.interfaces.cli query "add validation to a config model"
python3 -m repo_wiki.interfaces.cli retrieve "add validation to a config model" --format json
```

Inspect the local knowledge base:

```bash
python3 -m repo_wiki.interfaces.cli status
python3 -m repo_wiki.interfaces.cli doctor
python3 -m repo_wiki.interfaces.cli metrics
python3 -m repo_wiki.interfaces.cli repositories list
```

Generate a local benchmark report:

```bash
python3 -m repo_wiki.interfaces.cli benchmark report --output reports/mvp-results.md
```

## HTTP API

Start the lightweight server:

```bash
python3 -m repo_wiki.interfaces.cli api serve --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Retrieve context:

```bash
curl -X POST http://127.0.0.1:8000/v1/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"task":"add validation to a config model","language":"Python","max_tokens":4000}'
```

Optional FastAPI app factory:

```python
from repo_wiki.interfaces.http import create_app

app = create_app()
```

## MCP-Compatible Stdio

Start the stdio adapter:

```bash
python3 -m repo_wiki.interfaces.cli mcp serve
```

Example client command config:

```json
{
  "mcpServers": {
    "repo-wiki": {
      "command": "repo-wiki",
      "args": ["mcp", "serve"]
    }
  }
}
```

Implemented MCP-style tools:

- `retrieve_context`
- `search_knowledge`
- `inspect_repository`
- `submit_feedback`
- `list_feedback`

Example JSON-RPC tool call:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "retrieve_context",
    "arguments": {
      "task": "add FastAPI auth tests",
      "language": "Python",
      "framework": "FastAPI"
    }
  }
}
```

Successful responses include a `context_pack.v1` payload, citations when available, and a retrieval trace ID.
