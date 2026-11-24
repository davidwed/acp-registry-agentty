#!/bin/sh
# Refresh agentty/ from an agentty checkout (docs/acp-registry/ is the source of truth).
#
#   ./sync.sh /path/to/agentty
set -eu

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
src=${1:-}

if [ -z "$src" ] || [ ! -f "$src/docs/acp-registry/agent.json" ]; then
    echo "usage: $0 /path/to/agentty-checkout" >&2
    exit 2
fi

cp "$src/docs/acp-registry/agent.json" "$here/agentty/agent.json"
cp "$src/docs/acp-registry/icon.svg" "$here/agentty/icon.svg"

echo "synced from $src/docs/acp-registry/"
git -C "$here" diff --stat -- agentty 2>/dev/null || true
echo
echo "then: python3 validate.py --check-urls"
