# Security policy — `agentdraft-mcp`

## Reporting a vulnerability

If you believe you've found a security issue in this MCP server or
the AgentDraft service it talks to, please report it privately rather
than filing a public GitHub issue.

**Email:** security@agentdraft.io

Please include:

- A description of the issue and where in the code (file + line if you
  have it).
- A proof-of-concept or reproduction steps if available.
- Your assessment of impact (data exposure, auth bypass, privilege
  escalation, command injection from tool arguments, etc.).
- Whether you'd like public credit when the fix is announced.

We aim to acknowledge reports within **3 business days** and to
provide a status update within **7 business days**. We'll coordinate
a disclosure window with you before publishing details.

## Scope

In scope:

- The `agentdraft-mcp` package as published on PyPI.
- Any issue where a malicious MCP client could exfiltrate API keys,
  bypass the conflict engine, forge audit rows, or coerce the server
  into making unauthorized calls.

Out of scope (please report directly to the relevant project):

- Bugs in the upstream `mcp` Python SDK — report at
  <https://github.com/modelcontextprotocol/python-sdk>.
- Bugs in the `agentdraft` Python SDK — report via the SDK's
  [SECURITY.md](../python/SECURITY.md).
- Vulnerabilities that require a malicious dependency to already be
  installed on the user's machine.

## Trust model

The MCP server runs in the same process tree as the MCP host (Claude
Desktop, Cursor, Cline, etc.). Tool inputs come from the host. The
server validates inputs through the underlying `agentdraft` SDK,
which enforces the API contract on the server side — but the server
itself trusts the host's environment for the `AGENTDRAFT_API_KEY`. Do
not run this MCP server in an environment where untrusted code can
read your process environment.
