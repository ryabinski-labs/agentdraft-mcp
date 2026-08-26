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
# `zip` is not part of a minimal Linux image and is absent from our
# self-hosted runners, so the archive is written with Python's zipfile
# instead — the interpreter is already a hard requirement of this script.
# Entries are sorted and their timestamps pinned so two builds of the
# same tree produce byte-identical bundles.
PYTHON_CMD="${PYTHON:-python3}"
if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
  echo "error: python3 not on PATH; set PYTHON=/path/to/python3" >&2
  exit 1
fi
BUILD_DIR="$BUILD_DIR" OUTPUT="$OUTPUT" "$PYTHON_CMD" - <<'PYZIP'
import os
import zipfile

build_dir = os.environ["BUILD_DIR"]
output = os.environ["OUTPUT"]
# 1980-01-01, the zero of the DOS timestamp zip stores.
epoch = (1980, 1, 1, 0, 0, 0)

paths = []
for dirpath, dirnames, filenames in os.walk(build_dir):
    dirnames.sort()
    for name in sorted(filenames):
        full = os.path.join(dirpath, name)
        paths.append((os.path.relpath(full, build_dir), full))
paths.sort()

with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as bundle:
    for arcname, full in paths:
        info = zipfile.ZipInfo(arcname, date_time=epoch)
        info.compress_type = zipfile.ZIP_DEFLATED
        # Preserve only the executable bit; zipfile otherwise records the
        # build host's umask, which differs between a laptop and a runner.
        mode = 0o755 if os.access(full, os.X_OK) else 0o644
        info.external_attr = mode << 16
        with open(full, "rb") as fh:
            bundle.writestr(info, fh.read())
PYZIP

SIZE="$(du -h "$OUTPUT" | awk '{print $1}')"
echo "[mcpb] wrote $OUTPUT ($SIZE)"
echo "[mcpb] verify by dragging $OUTPUT into Claude Desktop → Settings → Extensions."
