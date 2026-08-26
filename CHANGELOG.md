# Changelog — `agentdraft-mcp`

All notable changes documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/).

## [0.1.1] — metadata points at a real repository

### Fixed

- `Repository`, `Issues`, and `Changelog` on the PyPI page all pointed at
  `github.com/GipsyChef/agentdraft` — an org that no longer exists — so every
  link from the package page 404'd. Release metadata cannot be edited after
  upload, which is why this is a new release rather than a correction.

### Added

- `server.json` (official MCP Registry) and `smithery.yaml` (Smithery), plus
  `REGISTRIES.md` documenting the submission runbook and the one thing
  blocking it: the source repository is private, and every MCP directory
  resolves a server through its public GitHub repo.

No tool surface changed.

## [0.1.0] — first PyPI release

### Added

- FastMCP-based server with six tools mapping 1:1 to the AgentDraft
  REST surface: `whoami`, `get_availability`, `create_hold`,
  `release_hold`, `commit_booking`, `cancel_booking`.
- Conflicts surface as a structured outranked payload (with
  `winning_agent_id`, `winning_agent_priority`, etc.) rather than
  string errors, so losing agents can branch on the result.
- `agentdraft-mcp` console script + `python -m agentdraft_mcp`
  entrypoint. Both run over stdio (the default transport every MCP
  host launches).
- README configured for Claude Desktop, Cursor, and generic stdio
  hosts.

### Notes

- Requires Python 3.10+.
- Auth via `AGENTDRAFT_API_KEY` env var (an `avs_live_…` agent key).
- Optional `AGENTDRAFT_BASE_URL` for dev environments.

[0.1.0]: https://pypi.org/project/agentdraft-mcp/0.1.0/
