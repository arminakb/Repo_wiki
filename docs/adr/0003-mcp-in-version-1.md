# ADR 0003: MCP Server in Version 1

Status: Accepted

## Context

The project is built for coding agents and modern AI-native workflows. Supporting MCP signals that the system was designed for agent ecosystems, not only traditional API usage.

## Decision

Include MCP server support in Version 1 after the core engine, CLI, and HTTP API.

Implementation order:

1. Core engine.
2. CLI.
3. HTTP API.
4. MCP server.

## Consequences

- The project becomes easier to integrate with agent tools.
- The portfolio presentation improves.
- The MCP adapter must remain thin and call the same core services as CLI/API.

## Alternatives Considered

- Delay MCP until after Version 1.
- Only expose HTTP API.

Both would reduce agent ecosystem readiness.
