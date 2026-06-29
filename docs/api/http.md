# HTTP API

Base URL:

```text
http://localhost:8000
```

Implemented endpoints:

- `GET /health`
- `POST /v1/ingest/repository`
- `POST /v1/ingest/local`
- `GET /v1/repositories`
- `GET /v1/repositories/{repo_id}`
- `GET /v1/knowledge`
- `POST /v1/retrieve`
- `POST /v1/feedback`
- `POST /v1/feedback/{stage_id}/promote`
- `POST /v1/feedback/{stage_id}/reject`
- `GET /v1/metrics`

Ingest endpoints accept `include` and `exclude` pattern arrays in addition to `license_policy`.
HTTP request payloads are validated with Pydantic models in both the optional FastAPI app and the standard-library server path.
`POST /v1/retrieve` accepts `repo`; when provided, candidates and returned citations are filtered to that repository.

`repo_wiki.interfaces.http.create_app()` provides the FastAPI app when FastAPI is installed. The CLI server keeps a standard-library fallback so the project remains runnable with only required dependencies.
