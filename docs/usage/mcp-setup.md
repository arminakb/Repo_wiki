# MCP Setup

Start the stdio adapter:

```bash
repo-wiki mcp serve
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

Available tools include retrieval, knowledge search, repository inspection, and feedback submission. Use `repo-wiki status` and `repo-wiki doctor` first if the agent cannot find context.
