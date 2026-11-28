#!/usr/bin/env bash
# Commit the current site as a single fresh commit and force-push it, so old
# MP3s don't pile up in git history. Run from the repo root after publish.py.
set -euo pipefail
cd "$(dirname "$0")/.."
git config user.name  "Podcast publisher"
git config user.email "podcasts@users.noreply.github.com"
git checkout -q --orphan publish-tmp
git add -A
git commit -q -m "Publish feed $(date -u +%Y-%m-%dT%H:%MZ)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
: "${GH_TOKEN:?set GH_TOKEN to the GitHub token}"
AUTH="Authorization: Basic $(printf 'x-access-token:%s' "$GH_TOKEN" | base64 -w0)"
git -c credential.helper= -c "http.extraHeader=$AUTH" push -q -f \
  https://github.com/markrflowers/mark-podcasts.git publish-tmp:main 2>&1 | grep -v -e "push negotiation" -e "expected 'acknowledgments'" || true
git checkout -q -B main publish-tmp && git branch -q -D publish-tmp
echo "pushed"
