#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

if ! git remote get-url upstream >/dev/null 2>&1; then
  git remote add upstream https://github.com/mattpocock/skills.git
fi

git fetch upstream
git merge --no-edit upstream/main
python3 scripts/generate-codex-compatibility.py
