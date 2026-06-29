# ADR 0006: Versioned SQLite and TOML Config

Status: Accepted

## Context

Phase 5 requires explicit storage versioning and reproducible local configuration. The project already uses SQLite and has a lightweight migration table plus an inline migration runner.

## Decision

Keep the lightweight SQLite migration runner in `repo_wiki.storage.sqlite` and expose the applied schema version through `SQLiteStore.schema_version()`.

Add `repo-wiki.toml` as the local configuration file. Environment variables remain overrides for scriptable runs and CI.

## Consequences

- Fresh databases record every applied migration in `schema_migrations`.
- Local runs can configure storage paths, file-size limits, default excludes, license policy, retrieval budget, and disabled LLM provider without shell state.
- No new dependency is needed because Python 3.11 includes `tomllib`.
