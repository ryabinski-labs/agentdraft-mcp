#!/usr/bin/env bash
# Build the AgentDraft MCP Desktop Extension bundle (.mcpb / .dxt).
#
# Output: sdks/mcp/dist/agentdraft-mcp.mcpb — a zip archive that a user
# can drag into Claude Desktop's Settings → Extensions to install
# AgentDraft without editing claude_desktop_config.json.
#
# Strategy: bundle the pip-installable `agentdraft-mcp` package (which
# transitively pulls in `agentdraft` and `mcp`) into the `server/lib`
# directory inside the bundle, with the manifest pointing PYTHONPATH at
# that lib dir. The bundle therefore needs only a host Python interpreter
# at runtime — no `pip install` step at install time.
#
# Run from the monorepo root:
#   bash sdks/mcp/scripts/build-mcpb.sh
#
# CI: invoked by .github/workflows/build-mcp-dxt.yml on each `mcp-v*` tag.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG_DIR="$ROOT/sdks/mcp"
DXT_SRC="$PKG_DIR/dxt"
BUILD_DIR="$PKG_DIR/build/dxt"
DIST_DIR="$PKG_DIR/dist"
OUTPUT="$DIST_DIR/agentdraft-mcp.mcpb"

if [[ ! -f "$DXT_SRC/manifest.json" ]]; then
  echo "error: $DXT_SRC/manifest.json missing — was the dxt/ tree committed?" >&2
  exit 1
fi
if [[ ! -f "$DXT_SRC/icon.png" ]]; then
  echo "warning: $DXT_SRC/icon.png missing — bundle will ship without an icon. Drop a 256x256 PNG before publishing to the registry." >&2
fi

echo "[mcpb] cleaning build tree…"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/server/lib"
mkdir -p "$DIST_DIR"

echo "[mcpb] copying manifest + entry point…"
cp "$DXT_SRC/manifest.json" "$BUILD_DIR/manifest.json"
cp "$DXT_SRC/server/main.py" "$BUILD_DIR/server/main.py"
if [[ -f "$DXT_SRC/icon.png" ]]; then
  cp "$DXT_SRC/icon.png" "$BUILD_DIR/icon.png"
fi

echo "[mcpb] resolving deps via pip into server/lib…"
PIP_CMD="${PIP:-pip}"
if ! command -v "$PIP_CMD" >/dev/null 2>&1; then
  echo "error: pip not on PATH; set PIP=/path/to/pip or activate a venv with pip" >&2
  exit 1
fi
# Install the published package; this transitively pulls in `agentdraft`
# and `mcp` (and httpx etc). For source builds, swap to `pip install -e .`
# from sdks/mcp.
#
# --no-compile keeps pip from precompiling .pyc — the bundle's installed
# Python may be 3.10, 3.11, 3.12, or 3.13, and .pyc files are version-
# specific, so any cache we ship is dead weight for everyone whose host
# Python doesn't happen to match the build host. Saves ~10MB uncompressed
# / ~3MB in the zip on a typical mcp install.
"$PIP_CMD" install --quiet --no-compile --target="$BUILD_DIR/server/lib" "$PKG_DIR"

# Belt-and-suspenders: scrub any __pycache__ that snuck in (e.g., from
# a dep whose setup.py prebuilds .pyc), then drop empty dirs.
find "$BUILD_DIR/server/lib" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$BUILD_DIR/server/lib" -type f -name "*.pyc" -delete

echo "[mcpb] zipping bundle…"
# Replace any prior bundle wholesale — `zip -r` left in place would
# *merge* into the existing archive, silently keeping deleted files
# (e.g. yesterday's __pycache__ noise) around in this release's .mcpb.
rm -f "$OUTPUT"
( cd "$BUILD_DIR" && zip -r -q -X "$OUTPUT" . )

SIZE="$(du -h "$OUTPUT" | awk '{print $1}')"
echo "[mcpb] wrote $OUTPUT ($SIZE)"
echo "[mcpb] verify by dragging $OUTPUT into Claude Desktop → Settings → Extensions."
