#!/bin/sh
# Copy the ready-made registry entry into a checkout of agentclientprotocol/registry.
#
#   ./apply.sh /path/to/registry-checkout
#
# The entry lands at <registry>/agentty/ — the registry scans top-level
# directories that contain an agent.json, and the directory name must equal the
# agent id. It is NOT agents/agentty/.
set -eu

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=${1:-}

if [ -z "$target" ]; then
    echo "usage: $0 /path/to/registry-checkout" >&2
    exit 2
fi
if [ ! -d "$target" ]; then
    echo "error: $target is not a directory" >&2
    exit 2
fi
if [ ! -f "$target/.github/workflows/build_registry.py" ]; then
    echo "error: $target does not look like a checkout of agentclientprotocol/registry" >&2
    exit 2
fi
if [ -e "$target/agentty" ]; then
    echo "error: $target/agentty already exists — refusing to overwrite" >&2
    exit 1
fi

mkdir -p "$target/agentty"
cp "$here/agentty/agent.json" "$target/agentty/agent.json"
cp "$here/agentty/icon.svg" "$target/agentty/icon.svg"

echo "copied agent.json + icon.svg into $target/agentty/"
echo
echo "next:"
echo "  cd $target"
echo "  uv run --with jsonschema .github/workflows/build_registry.py"
echo "  python3 .github/workflows/verify_agents.py --auth-check --agent agentty"
