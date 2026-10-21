"""agentdraft-mcp — MCP server for the AgentDraft coordination layer.

Exposes AgentDraft as a set of tools any MCP-aware AI client (Claude
Desktop, Cursor, Cline, custom Claude Agent SDK / OpenAI Agents SDK
runtimes) can call. The server is a thin wrapper over the public REST
API via the ``agentdraft`` Python SDK — there is no separate engine
path.

Quickstart::

    pip install agentdraft-mcp
    AGENTDRAFT_API_KEY=avs_live_… agentdraft-mcp
"""

# Define __version__ BEFORE any submodule import so submodules can read
# it via `from . import __version__` without tripping a partial-import
# error (the submodules use the version to compose their User-Agent).
__version__ = "0.2.0"

from .server import build_server

__all__ = ["build_server"]
