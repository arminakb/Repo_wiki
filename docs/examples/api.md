# API Examples

Start the HTTP API:

```bash
python3 -m repo_wiki.interfaces.cli api serve --host 127.0.0.1 --port 8000
```

FastAPI integrations can import the optional app factory:

```python
from repo_wiki.interfaces.http import create_app

app = create_app()
```

Ingest a local repository with filters:

```bash
curl -X POST http://localhost:8000/v1/ingest/local \
  -H 'Content-Type: application/json' \
  -d '{"path":"./my-project","include":["**/*.py","**/*.md"],"exclude":["build/**"],"license_policy":"private_local_only"}'
```

Retrieve context:

```bash
curl -X POST http://localhost:8000/v1/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"task":"implement password reset in Next.js with Prisma","language":"TypeScript","framework":"Next.js","max_tokens":4000}'
```

Health:

```bash
curl http://localhost:8000/health
```
