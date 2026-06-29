# CLI Examples

Current module form:

```bash
python3 -m repo_wiki.interfaces.cli init
python3 -m repo_wiki.interfaces.cli ingest local ./my-project
python3 -m repo_wiki.interfaces.cli ingest local ./my-project --include "**/*.py" --exclude "build/**"
python3 -m repo_wiki.interfaces.cli ingest github https://github.com/example/project
python3 -m repo_wiki.interfaces.cli ingest status job_123
python3 -m repo_wiki.interfaces.cli extract <repo_id>
python3 -m repo_wiki.interfaces.cli compile <repo_id> --no-llm
python3 -m repo_wiki.interfaces.cli retrieve "implement password reset in Next.js with Prisma"
python3 -m repo_wiki.interfaces.cli retrieve "add FastAPI endpoint with tests" --language Python --framework FastAPI --license-policy permissive_only
python3 -m repo_wiki.interfaces.cli knowledge list --type ImplementationPattern
python3 -m repo_wiki.interfaces.cli repositories list
python3 -m repo_wiki.interfaces.cli repositories show <repo_id>
python3 -m repo_wiki.interfaces.cli graph export --format mermaid --output docs/diagrams/knowledge.graph.mmd
python3 -m repo_wiki.interfaces.cli feedback promote <stage_id> --reason "reviewed"
python3 -m repo_wiki.interfaces.cli feedback reject <stage_id> --reason "duplicate"
python3 -m repo_wiki.interfaces.cli metrics
python3 -m repo_wiki.interfaces.cli backup create /tmp/repo-wiki-backup.sqlite
python3 -m repo_wiki.interfaces.cli backup restore /tmp/repo-wiki-backup.sqlite
python3 -m repo_wiki.interfaces.cli benchmark run --suite mvp
python3 -m repo_wiki.interfaces.cli benchmark report --output docs/benchmarks/mvp-results.md
```

Installed script form:

```bash
repo-wiki init
repo-wiki ingest local ./my-project
repo-wiki ingest status job_123
repo-wiki retrieve "implement password reset in Next.js with Prisma"
repo-wiki repositories list
repo-wiki backup create /tmp/repo-wiki-backup.sqlite
repo-wiki benchmark run --suite mvp
repo-wiki benchmark report --output docs/benchmarks/mvp-results.md
```
