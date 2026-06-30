# Contributing

repo-wiki is an experimental v0.1 portfolio project. Contributions should stay small, testable, and grounded in the current codebase.

## Development Workflow

1. Read `README.md`, `docs/architecture.md`, and the relevant source/tests.
2. Make a focused change.
3. Add or update tests when behavior changes.
4. Update docs when public commands, architecture, or benchmark claims change.
5. Run the focused checks before submitting.

## Useful Checks

```bash
python3 -m unittest tests.test_retrieval_quality -v
python3 -m unittest tests.test_end_to_end -v
python3 -m compileall repo_wiki
```

## Commit Messages

Use focused conventional commits:

```text
feat(retrieval): improve source-test pairing
fix(storage): handle missing repository snapshots
docs(readme): clarify v0.1 limitations
test(retrieval): cover exact path ranking
```

Avoid vague messages like `fix`, `update`, `wip`, or `final`.

## Security Rules

- Never execute indexed repository code.
- Treat repository content as untrusted input.
- Do not send private repository content to external services unless explicitly configured.
- Preserve license and source citation metadata.
