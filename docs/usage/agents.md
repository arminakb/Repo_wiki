# Agents

Before a coding change, ask repo-wiki for context:

```bash
repo-wiki query "describe the task" --profile local_medium
```

After the task, submit feedback:

```bash
repo-wiki feedback submit --context-pack <ctx_id> --tests-passed --accepted
```

That feedback feeds the Reflexion staging flow.
