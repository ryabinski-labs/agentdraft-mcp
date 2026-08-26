"""Entrypoint: ``python -m agentdraft_mcp`` or the ``agentdraft-mcp``
console script. Runs the server over stdio, which is the default
transport every MCP client (Claude Desktop, Cursor, Cline) launches via
a subprocess.
"""

from .server import build_server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
