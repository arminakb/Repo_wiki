# MCP Examples

Start the MCP-compatible stdio adapter:

```bash
python3 -m repo_wiki.interfaces.cli mcp serve
```

Implemented MCP-style tools:

- `retrieve_context`
- `search_knowledge`
- `inspect_repository`
- `submit_feedback`

Example `retrieve_context` input:

```json
{
  "task": "implement password reset in Next.js with Prisma",
  "language": "TypeScript",
  "framework": "Next.js",
  "max_tokens": 4000
}
```

Example `inspect_repository` input:

```json
{
  "repo_id": "repo_123"
}
```

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

Successful `retrieve_context` transcript shape:

```json
{
  "context_pack": {
    "schema_version": "context_pack.v1",
    "task": "add FastAPI auth tests",
    "recommended_patterns": [],
    "source_citations": []
  },
  "citations": [],
  "trace_id": "trace_..."
}
```

Supported resources:

- `repo-wiki://metrics`
- `repo-wiki://repositories`
- `repo-wiki://repositories/{repo_id}`
- `repo-wiki://knowledge/{knowledge_object_id}`
- `repo-wiki://context-packs/{context_pack_id}`
