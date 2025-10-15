#!/usr/bin/env bash
set -euo pipefail
if ! command -v gh >/dev/null; then
  echo '{"ok":false,"error":"gh CLI not installed"}' >&2
  exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo '{"ok":false,"error":"gh not authenticated"}' >&2
  exit 1
fi
