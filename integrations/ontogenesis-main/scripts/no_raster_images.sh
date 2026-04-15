#!/usr/bin/env bash
set -euo pipefail
bad="$(git ls-files | grep -E "\\.(png|jpg|jpeg|webp|gif)$" || true)"
if [ -n "$bad" ]; then
  echo "ERR: Raster images tracked:"
  echo "$bad"
  exit 2
fi
echo "OK: no raster images tracked"
