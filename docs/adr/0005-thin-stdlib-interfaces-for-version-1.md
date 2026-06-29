# ADR 0005: Thin Standard-Library Interfaces for Version 1

Status: Accepted

## Context

SAS recommends Typer for CLI ergonomics, FastAPI as the production HTTP path, and the official MCP SDK for MCP compatibility. The current implementation already exposes the required CLI, HTTP, and MCP contracts with `argparse`, a dependency-free stdlib HTTP server, an optional FastAPI app factory, and a JSON-RPC stdio MCP adapter.

## Decision

Keep the Version 1 public interfaces thin and dependency-light:

- Keep `argparse` for the CLI until command complexity requires Typer.
- Keep the stdlib HTTP server as the runnable production fallback.
- Keep `create_app()` as the optional FastAPI integration path with Pydantic request models.
- Keep the MCP adapter as JSON-RPC stdio and route all tools/resources through core services.

## Consequences

- A clean checkout remains runnable with Python plus Pydantic only.
- Interface behavior is covered by contract tests instead of framework-specific machinery.
- Future Typer, FastAPI-only, or official MCP SDK migrations must preserve the same core-service calls and response shapes.

## Alternatives Considered

- Migrate CLI to Typer during Phase 3.
- Require FastAPI for serving HTTP.
- Require the official MCP SDK immediately.

These add dependencies and migration work without improving the current Version 1 contract surface.
