# Contributing

Repo Knowledge Compiler is designed for human and agent contributors.

Read first:

- `SAS.md`
- `AGENT.md`
- `ARCHITECTURE.md`
- `ROADMAP.md`
- `DECISIONS.md`

## Development Workflow

1. Pick a roadmap phase or issue.
2. Read the relevant section of `SAS.md`.
3. Make a focused change.
4. Add or update tests.
5. Update docs if behavior or architecture changes.
6. Use a conventional commit message.

## Commit Messages

Use:

```text
feat(storage): implement sqlite metadata layer
feat(parser): add python ast extraction pipeline
feat(retrieval): add hybrid lexical retrieval
feat(mcp): add retrieve_context tool
docs(architecture): add retrieval planner design
test(storage): cover repository snapshot persistence
```

Avoid:

```text
fix
update
wip
final
test
```

## Architecture Changes

If a change affects storage, retrieval, graph schema, API contracts, MCP tools, scaling strategy, or license/privacy policy, add or update an ADR in `docs/adr/`.

## Testing Expectations

Add tests for:

- domain model validation.
- storage writes.
- parser output.
- retrieval ranking.
- context pack generation.
- CLI/API/MCP contracts.

## Security Rules

- Never execute indexed repository code.
- Treat repository content as untrusted input.
- Do not send private repository content to external LLMs unless explicitly configured.
- Preserve license and source citation metadata.
