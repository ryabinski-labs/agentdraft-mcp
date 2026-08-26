"""Entry point for the AgentDraft MCP Desktop Extension bundle.

The bundle ships ``agentdraft_mcp`` and its dependencies under
``server/lib`` (set as ``PYTHONPATH`` in the manifest's ``mcp_config``)
so a user can drag-drop the ``.mcpb`` into Claude Desktop without
needing pip on their PATH. The bundle still requires a system Python
interpreter — that constraint is in the manifest's
``compatibility.runtimes.python`` requirement.

Authentication is via ``AGENTDRAFT_API_KEY``, populated from the user's
``user_config.api_key`` at install time and surfaced to this process
via env var by Claude Desktop's MCP host.
"""

from __future__ import annotations

import sys


def main() -> None:
    try:
        from agentdraft_mcp.server import build_server
    except ImportError as exc:  # pragma: no cover — bundle integrity
        sys.stderr.write(
            "Failed to import agentdraft_mcp. The Desktop Extension bundle "
            "appears incomplete; reinstall the .mcpb. Underlying error: "
            f"{exc}\n",
        )
        sys.exit(1)

    build_server().run()


if __name__ == "__main__":
    main()
