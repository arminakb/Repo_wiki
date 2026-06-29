# MCP Integration

MCP support is required in Version 1.

The MCP server exposes:

- `retrieve_context`
- `search_knowledge`
- `inspect_repository`
- `submit_feedback`

The MCP adapter remains thin. It validates input, calls core services, and returns structured output. Official SDK adoption should be a wrapper around the same service calls, not a second implementation.
