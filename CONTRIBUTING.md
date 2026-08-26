# Contributing — `agentdraft-mcp`

Thanks for considering a contribution.

[`ryabinski-labs/agentdraft-mcp`](https://github.com/ryabinski-labs/agentdraft-mcp)
is a **published mirror**. The source of truth is the `sdks/mcp` directory of
AgentDraft's application repository, which is private, and each release
replaces the mirror's contents wholesale. Issues and pull requests opened on
the mirror are read and answered — a change we take is applied upstream and
appears here on the next sync, rather than being merged in place. That is why
a merged-looking PR may close as "applied upstream": the commit is real, it
just carries a different SHA.

## Before you start

- The server is intentionally thin: every tool maps 1:1 to a method on the
  `agentdraft` Python SDK. If you want to expose new behavior, it belongs in
  the SDK first; the MCP layer should not grow parallel logic.
- For a new tool, open an issue before writing code — the tool surface is
  versioned and adding to it is a compatibility decision.
- For bug fixes and docs, just send a PR.

## Local development

```bash
git clone https://github.com/ryabinski-labs/agentdraft-mcp
cd agentdraft-mcp

python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run the server interactively against a local AgentDraft
AGENTDRAFT_BASE_URL=http://localhost:8080 \
AGENTDRAFT_API_KEY=avs_live_dev_... \
  agentdraft-mcp
```

Test against Claude Desktop by editing your `claude_desktop_config.json` to
point at the local install via `command: python` and
`args: ["-m", "agentdraft_mcp"]`.

## PRs

- Keep the diff small. One concern per PR.
- Update [CHANGELOG.md](CHANGELOG.md) under an `## [Unreleased]` section.
- Conventional Commits for messages — `feat:`, `fix:`, `docs:`, `chore:`.

## Reporting security issues

Do **not** open a public issue. Follow [SECURITY.md](SECURITY.md).
