# MCP Tools

Current MCP-compatible stdio adapter tools:

## retrieve_context

Returns a cited context pack for a coding task.
The optional `repo` argument is enforced during retrieval, so returned citations stay within that repository.

## search_knowledge

Searches stored knowledge objects.

## inspect_repository

Returns repository metadata and snapshots for a `repo_id`.

## submit_feedback

Submits feedback for a context pack and records Reflexion signals.

## list_feedback

Lists staged Reflexion feedback records, filtered by status when provided.

## Resources

The stdio adapter also supports:

- `resources/list`
- `resources/read` for `repo-wiki://metrics`
- `resources/read` for `repo-wiki://repositories`
- `resources/read` for `repo-wiki://repositories/{repo_id}`
- `resources/read` for `repo-wiki://knowledge/{knowledge_object_id}`
- `resources/read` for `repo-wiki://context-packs/{context_pack_id}`
- `resources/read` for `repo-wiki://feedback`

The adapter keeps protocol handling thin: parse JSON-RPC input, call core services, return structured JSON. If the official MCP SDK is installed later, it should wrap the same `call_tool` and resource functions rather than duplicating retrieval logic.
