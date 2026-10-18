#!/usr/bin/env bash
set -euo pipefail
# Keep Linux dependencies in WSL, separately from Windows node_modules.
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
workspace_dir="${XDG_DATA_HOME:-$HOME/.local/share}/jinyun-teacher-workspace"
mkdir -p "$workspace_dir"
rsync -a --exclude=node_modules --exclude=dist --exclude=.git "$repo_root/admin-web/" "$workspace_dir/"
cd "$workspace_dir"
if [[ ! -d node_modules ]] || ! cmp -s pnpm-lock.yaml .installed-lock.yaml; then
  npx --yes pnpm@11.25.0 install --frozen-lockfile
  cp pnpm-lock.yaml .installed-lock.yaml
fi
if [[ "${1:-dev}" == "build" ]]; then
  npx --yes pnpm@11.25.0 build
else
  exec npx --yes pnpm@11.25.0 dev --host 0.0.0.0 --port 5173 --strictPort
fi
