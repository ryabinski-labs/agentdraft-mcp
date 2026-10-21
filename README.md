# agentdraft-mcp — MCP server for AgentDraft

[![PyPI](https://img.shields.io/pypi/v/agentdraft-mcp.svg)](https://pypi.org/project/agentdraft-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An [MCP](https://modelcontextprotocol.io/) server that exposes
[AgentDraft](https://agentdraft.io) — the ops API for AI agents with
inbox, conflict-free calendar, and audit tools — as a set of tools any
MCP-aware AI client can call.

Use this if your agent runtime is Claude Desktop, Claude Code, Cursor,
Cline, an OpenAI Agents SDK app, or any other MCP host. The server is
a thin wrapper around the [`agentdraft`](https://pypi.org/project/agentdraft/)
Python SDK — same auth, same errors, same semantics as the REST API
and the language SDKs.

## Tools

Nine tools, grouped by what they coordinate:

- **Scheduling** — `whoami`, `get_availability`, `create_hold`, `release_hold`,
  `commit_booking`, `cancel_booking`.
- **Human approval** — `request_approval`, `get_approval`, `wait_for_approval`.
  Open a gate before a consequential action and resume only when a person
  decides. The wait is clamped to 120 seconds; a timeout returns
  `status: "pending"`, never a false approval.

```python
approval = await tools.request_approval(
    action_type="deploy.production",
    summary="Ship v0.2.0 to production",
    evidence={"commit": "a1b2c3d", "migrations": 2},
)
result = await tools.wait_for_approval(approval["approval_id"], timeout_seconds=60)
if result["status"] != "approved":
    raise SystemExit(f"stood down: {result['status']}")
```

An interactive config generator for every supported host lives at
<https://agentdraft.io/for-agents/mcp>.

## Install

```bash
pip install agentdraft-mcp
```

Requires Python 3.10+ and a valid `avs_live_…` agent key from the
AgentDraft dashboard.

## Upgrade

```bash
pip install -U agentdraft-mcp
```

Release notes: <https://agentdraft.io/changelog>

## Configure your MCP client

`agentdraft-mcp` is on PyPI, so once it's installed the JSON config below
works on any MCP host right now — no extra downloads.

### Claude Desktop / Claude Code — JSON config (recommended)

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or the equivalent on Windows/Linux:

```json
{
  "mcpServers": {
    "agentdraft": {
      "command": "agentdraft-mcp",
      "env": {
        "AGENTDRAFT_API_KEY": "avs_live_..."
      }
    }
  }
}
```

### Cursor / Cline / generic stdio host

```json
{
  "mcpServers": {
    "agentdraft": {
      "command": "python",
      "args": ["-m", "agentdraft_mcp"],
      "env": {
        "AGENTDRAFT_API_KEY": "avs_live_..."
      }
    }
  }
}
```

For local development against a dev backend, also set
`AGENTDRAFT_BASE_URL=http://localhost:8080`.

### Claude Desktop — `.mcpb` Desktop Extension (drag-drop)

Each release also ships a `.mcpb` Desktop Extension bundle on
[GitHub Releases](https://github.com/ryabinski-labs/agentdraft-mcp/releases). Drag `agentdraft-mcp.mcpb` into Claude
Desktop → **Settings → Extensions** and paste your `avs_live_…` API key — no
JSON editing, no `pip install`.

## Tools

| Tool | Purpose |
|---|---|
| `whoami` | Confirm the API key and return the agent's identity, priority, scopes, and the owner's `timezone` |
| `get_availability` | List slots open to the calling agent in [start, end) |
| `create_hold` | Reserve a slot tentatively (30 s TTL); optional `title` / `invitee` |
| `release_hold` | Release a hold so other agents can claim it |
| `commit_booking` | Finalize a booking — atomic compare-and-swap; optional `title` / `invitee` |
| `cancel_booking` | Cancel a committed booking the calling agent owns |

All times are ISO 8601 strings (`2026-06-01T14:00:00Z`). All write
tools accept an `idempotency_key` for safe retries. `create_hold` and
`commit_booking` also accept an optional `title` and `invitee`
(`{name, email, notes}`) recording who the slot is for — surfaced to the
owner in the dashboard.

## How conflicts surface

When two agents race for the same slot, exactly one wins. Losing
agents receive a structured outranked payload — not a string error:

```json
{
  "error": "outranked",
  "winning_booking_id": "bkg_…",
  "winning_agent_id": "agt_…",
  "winning_agent_priority": 1,
  "your_priority": 3,
  "message": "Your booking was outranked. Read winning_agent_id and propose an alternate slot rather than retrying."
}
```

Your agent should branch on this and propose an alternate, not retry
the same slot.

## How this differs from the AgentDraft SDKs

| | Python/TS SDK | MCP server |
|---|---|---|
| **Caller** | App code you wrote | An AI client (Claude Desktop, etc.) |
| **Transport** | HTTPS direct to api.agentdraft.io | stdio between the MCP host and this process |
| **Auth** | `Client(api_key=…)` | `AGENTDRAFT_API_KEY` env var |
| **Semantics** | Same | Same |
| **Errors** | Typed Python exceptions | Structured JSON in the tool result |

Use the SDK when *you* are writing the agent. Use this MCP server when
*someone else's* agent runtime (Claude Desktop, Cursor, Cline,
generic MCP host) needs to call AgentDraft on a user's behalf without
custom code.

## Links

- Protocol spec: <https://agentdraft.io/spec>
- API docs: <https://agentdraft.io/docs>
- Changelog: <https://agentdraft.io/changelog>
- Python SDK: [`agentdraft`](https://pypi.org/project/agentdraft/)
- TypeScript SDK: [`agentdraft`](https://www.npmjs.com/package/agentdraft)
- Source: <https://github.com/ryabinski-labs/agentdraft-mcp>
- Issues: <https://github.com/ryabinski-labs/agentdraft-mcp/issues>

## Security

Found a vulnerability? See [SECURITY.md](SECURITY.md). Do **not** open
a public issue for a security report.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). [`ryabinski-labs/agentdraft-mcp`](https://github.com/ryabinski-labs/agentdraft-mcp)
is a published mirror of a directory in AgentDraft's private application
repository — issues and pull requests are read there, and land back through
the next release sync.

## License

MIT — see [LICENSE](LICENSE).
