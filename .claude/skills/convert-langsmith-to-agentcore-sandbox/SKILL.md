---
name: convert-langsmith-to-agentcore-sandbox
description: Convert a deepagents script from the LangSmith sandbox backend (SandboxClient/LangSmithSandbox) to the AWS Bedrock AgentCore Code Interpreter sandbox backend (CodeInterpreter/AgentCoreSandbox). Use when a python/m2 (or similar) script imports deepagents.backends.langsmith.LangSmithSandbox or langsmith.sandbox.SandboxClient and the user wants it switched to langchain-agentcore-codeinterpreter.
---

# Convert LangSmith sandbox -> AgentCore sandbox

## When to use this

A script creates a deep agent sandbox backend like this:

```python
from deepagents.backends.langsmith import LangSmithSandbox
from langsmith.sandbox import SandboxClient

client = SandboxClient()
ls_sandbox = client.create_sandbox(name="...")
backend = LangSmithSandbox(sandbox=ls_sandbox)
...
client.delete_sandbox(ls_sandbox.name)
```

and the user wants it running on AWS Bedrock AgentCore's Code Interpreter
instead (package `langchain-agentcore-codeinterpreter`, already a project
dependency — check `pyproject.toml` / `uv.lock` before assuming it needs
installing).

## Mechanical conversion

Replace the imports:

```python
# before
from deepagents.backends.langsmith import LangSmithSandbox
from langsmith.sandbox import SandboxClient

# after
import os
from bedrock_agentcore.tools.code_interpreter_client import CodeInterpreter
from langchain_agentcore_codeinterpreter import AgentCoreSandbox
```

Replace sandbox creation:

```python
# before
client = SandboxClient()
ls_sandbox = client.create_sandbox(name=f"lca-deepagents-lab-{uuid4().hex[:8]}")
print(f"Sandbox: {ls_sandbox.name}  (id: {ls_sandbox.id})")
backend = LangSmithSandbox(sandbox=ls_sandbox)

# after
region = os.environ.get("AWS_REGION", "us-west-2")
interpreter = CodeInterpreter(region)
session_id = interpreter.start(name=f"lca-deepagents-lab-{uuid4().hex[:8]}")
print(f"Sandbox session: {session_id}  (region: {region})")
backend = AgentCoreSandbox(interpreter=interpreter)
```

Replace teardown:

```python
# before
finally:
    client.delete_sandbox(ls_sandbox.name)

# after
finally:
    interpreter.stop()
```

`AgentCoreSandbox` implements the same `SandboxBackendProtocol` as
`LangSmithSandbox` (inherits from `deepagents.backends.sandbox.BaseSandbox`),
so `backend.upload_files(...)`, `backend.execute(...)`, and
`backend.download_files(...)` all keep working unchanged.

### File download differs slightly

`LangSmithSandbox`-based scripts sometimes read a file straight off the
`ls_sandbox` object (`ls_sandbox.read(path)` returning raw bytes). There is
no equivalent on `interpreter`/`AgentCoreSandbox` — use the protocol method
on `backend` instead, which returns a list of `FileDownloadResponse`
(`.path`, `.content`, `.error`):

```python
# before
png_bytes = ls_sandbox.read("/genre_revenue.png")
out_path.write_bytes(png_bytes)

# after
download_results = backend.download_files(["/genre_revenue.png"])
download_result = download_results[0]
if download_result.error:
    raise RuntimeError(f"Failed to download {download_result.path}: {download_result.error}")
out_path.write_bytes(download_result.content)
```

## Gotchas to flag to the user, don't silently "fix"

- **Region**: no region is read from `.env` for AgentCore. Default to
  `us-west-2` (matching the SDK's own docstring examples) but read
  `AWS_REGION` from the environment first, and tell the user to check it
  matches where their AgentCore Code Interpreter is available. AWS
  credentials must already be configured (same as for Bedrock models).
- **Sandbox working directory is not `/`**: AgentCore's writable root maps
  to something like `/opt/amazon/genesis1p-tools/var/`, not `/`. Files the
  system prompt/task tells the agent to read or write "at /chinook.db" or
  "to /genre_revenue.png" actually land under that real cwd — the agent
  generally figures this out on its own and reports where it put things,
  and `download_files`/`upload_files` handle path resolution internally, so
  don't rewrite the task's paths — just don't be surprised when the
  agent's answer mentions a different absolute path than the prompt used.
- **A stray `ConflictException` after everything already worked is
  harmless.** After the script's own logic completes (agent answered,
  chart/file downloaded and saved to disk), you may see a traceback like:

  ```
  botocore.errorfactory.ConflictException: ... session ... was terminated
  on user request before the request could complete.
  ```

  This happens when `interpreter.stop()` runs in `finally` while some
  background call issued by the SDK's dedicated thread pool
  (`_AGENTCORE_EXECUTOR`) is still in flight. Verify the actual deliverable
  (e.g. the downloaded PNG) exists and is valid before treating the run as
  failed — check file size/`file <path>` output, not just the presence of a
  traceback in stdout/stderr.

## Verification

After converting, run the script for real (it needs live AWS credentials)
and confirm:
1. It prints a sandbox session id and doesn't raise during startup.
2. The agent's final message text looks sane for the task.
3. Any downloaded artifact (image, file) exists on disk afterward and is a
   valid file of that type — don't just trust exit code 0, since the
   stray-ConflictException gotcha above can make a successful run look like
   it errored in the log tail.
