#!/usr/bin/env bash
# Package the app for deploy/remote-deploy.sh: the source plus the built front end.
#   (cd frontend && npm ci && npm run build) && deploy/package.sh /tmp/dsa-src.tgz
# Run from the repo root. Write the archive outside the tree.
set -euo pipefail

out=${1:?usage: deploy/package.sh OUT.tgz}
[[ -f frontend/dist/index.html ]] || { echo "frontend/dist is missing: run npm run build in frontend/ first" >&2; exit 1; }

COPYFILE_DISABLE=1 tar czf "$out" --no-xattrs \
  --exclude=.git --exclude=.git-pre-github --exclude=.github --exclude=node_modules \
  --exclude=.venv --exclude=tests --exclude=__pycache__ --exclude=data --exclude=.env \
  --exclude='*.db' --exclude='*.db-*' --exclude=.DS_Store \
  .
